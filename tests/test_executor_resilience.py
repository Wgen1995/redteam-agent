# -*- coding: utf-8 -*-
"""F22 工具执行器韧性三件（能力对照总账第一优先补件）——TDD 红转绿。

对齐 docs/design/2026-10-20-capability-comparison-ledger.md §F22 最优方案：
  件a 异步 execution_id：长任务（阈值可配，默认 60s）发卡即回 execution_id，
      后台线程续跑不占战士轮次，结果后续轮次自动回填（轮询续接），
      状态行落 goal 目录可回放，进程重启孤儿对账（CSAI execution_service
      同型：有界等待+get/wait 轮询续接——冲击#7「值得整体抄」）；
  件b 卡层断路器：连续 N 失败（默认 3）熔断该卡冷却（默认 15min），
      llmpool 分道冷却同型移植（连续计数→熔断→冷却窗→惰性到期→成功治愈
      →状态落盘→事件入账）；判定拦截类拒绝不计失败（llmpool no_failover
      同型：保守不动计数）；
  件c 超大输出 spill：输出超阈值（默认 1MB）落盘 goal 目录 tmp 文件，
      上下文只进摘要+指针（防炸脑），全文留档可取回（不丢果）。

金样纪律：同输入同 execution 行为——阈值未触达（快工具/小输出/失败未连三）
时 outcomes 与事件行必须与三件落地前逐字节同形（件d 金样钉测）。

跑法：python3 -m unittest tests.test_executor_resilience -v
"""
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from warrior.executor import ToolBatchExecutor  # noqa: E402

W = "warrior:W-1"


class Rec(object):
    """add_tl 假件：事件行录制。"""

    def __init__(self):
        self.events = []

    def __call__(self, event, ts):
        self.events.append(event)

    def has(self, frag):
        return any(frag in e for e in self.events)


class Clock(object):
    """可拨浮点钟（断路器冷却窗惰性到期用）。"""

    def __init__(self, t=1770000000.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, d):
        self.t += float(d)


class LedgerFake(object):
    def __call__(self, cmd, args):
        return 0, "ok"


def tool(card, *args):
    return {"op": "tool", "card": card, "args": list(args)}


class Probe(object):
    """可编程工具执行面：结果可按卡名（dict，并行批安全）或按序（list，
    单刀序安全）回放；记调用数（线程安全——并行批探针）。"""

    def __init__(self, results=None, default=(0, "ok-out", "")):
        self._lock = threading.Lock()
        self.calls = []
        self.by_card = dict(results) if isinstance(results, dict) else {}
        self.queue = list(results) if isinstance(results, list) else []
        self.default = default

    def __call__(self, card, args):
        with self._lock:
            self.calls.append((card, list(args)))
            if card in self.by_card:
                return self.by_card[card]
            if self.queue:
                return self.queue.pop(0)
            return self.default


class ResilienceCase(unittest.TestCase):
    """直挂 ToolBatchExecutor（端口注入假件，零真外呼零 LLM）。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.gd, ignore_errors=True)
        self.rec = Rec()

    def make(self, probe, clock=None, **kw):
        args = dict(tool_exec=probe, ledger_write=LedgerFake(),
                    now=clock or Clock(), ts=lambda: "2026-10-20T00:00:00Z",
                    add_tl=self.rec, warrior_id=W)
        args.update(kw)
        return ToolBatchExecutor(**args)

    # ---- 件d 金样：同输入同 execution 行为 ------------------------------

    def test_gold_outcomes_byte_identical_when_thresholds_idle(self):
        """快工具+小输出+失败未连三：outcomes/事件行与三件前逐字节同形。"""
        probe = Probe(results={          # 按卡名回放（并行批零竞态）
            "dig": (0, "ok-out", ""),
            "curl": (1, "", "gate 侧失败"),
        })
        ex = self.make(probe, goal_dir=self.gd)
        res = ex.execute([
            tool("dig", "+short", "A", "a.shop.example"),
            tool("curl", "-sS", "https://b.shop.example/"),
            {"op": "note", "text": "中段留言"},
            {"op": "ledger", "cmd": "add-fact",
             "args": {"kind": "info", "target": "shop.shop.example",
                      "detail": "d", "confidence": "0.7"}},
        ], "IN-0007", 1)
        self.assertEqual(res.outcomes, [
            "tool dig rc=0 out=ok-out err=",
            "tool curl rc=1 out= err=gate 侧失败",
            "note: 中段留言",
            "ledger add-fact rc=0 ok",
        ])
        self.assertEqual(self.rec.events, [
            "warrior-progress warrior=%s intent=IN-0007 turn=1 op=tool "
            "card=dig rc=0 call=0" % W,
            "warrior-progress warrior=%s intent=IN-0007 turn=1 op=tool "
            "card=curl rc=1 call=1" % W,
            "warrior-progress warrior=%s intent=IN-0007 turn=1 op=ledger "
            "cmd=add-fact rc=0" % W,
        ], "事件行格式必须与三件落地前逐字节一致（金样纪律）")

    # ---- 件c 超大输出 spill ---------------------------------------------

    def test_spill_writes_file_and_context_gets_pointer(self):
        """输出超 1MB：全文落盘 goal 目录 tmp，上下文只进摘要+指针。"""
        big = "A" * 600000 + "B" * 600000
        probe = Probe(results=[(0, big, "")])
        ex = self.make(probe, goal_dir=self.gd)
        res = ex.execute([tool("dig", "+short", "A", "a.shop.example")],
                         "IN-0007", 1)
        tmp_dir = os.path.join(self.gd, "tmp")
        files = os.listdir(tmp_dir)
        self.assertEqual(len(files), 1, "恰落一个 spill 文件")
        path = os.path.join(tmp_dir, files[0])
        self.assertTrue(files[0].startswith("spill-dig-"),
                        "spill 文件名带卡名: %s" % files[0])
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), big, "全文留档不丢果")
        out = res.outcomes[0]
        self.assertLess(len(out), 800, "上下文面只进摘要+指针（防炸脑）")
        self.assertIn("spill=", out)
        self.assertIn(path, out, "指针=可取回的落盘路径")
        self.assertNotIn("AAAA", out[:40], "超限原文不得整段入上下文")
        self.assertTrue(out.startswith("tool dig rc=0"),
                        "outcome 保持 tool 卡面格式")

    def test_spill_under_threshold_no_file(self):
        """输出未超阈值：零 spill 文件，outcome 经典格式不变（金样）。"""
        probe = Probe(results=[(0, "small", "")])
        ex = self.make(probe, goal_dir=self.gd)
        res = ex.execute([tool("dig", "+short", "A", "a.shop.example")],
                         "IN-0007", 1)
        self.assertEqual(res.outcomes, ["tool dig rc=0 out=small err="])
        self.assertFalse(os.path.exists(os.path.join(self.gd, "tmp")))

    def test_spill_deterministic_same_content_same_path(self):
        """同输出两次 spill：内容哈希命名=同路径（同输入同行为金样律）。"""
        big = "X" * 1_100_000
        probe = Probe(results=[(0, big, ""), (0, big, "")])
        ex = self.make(probe, goal_dir=self.gd)
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 1)
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 2)
        files = os.listdir(os.path.join(self.gd, "tmp"))
        self.assertEqual(len(files), 1, "同内容同路径不重复落盘")

    # ---- 件b 卡层断路器 --------------------------------------------------

    def test_breaker_trips_after_three_consecutive_failures(self):
        """连续 3 败熔断：第 4 次调用秒拒不再执行，trip 事件入账。"""
        probe = Probe(default=(1, "", "gate 侧失败"))
        ex = self.make(probe, goal_dir=self.gd, breaker_rng=lambda: 0.5)
        for t in (1, 2, 3):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 4)
        self.assertEqual(len(probe.calls), 3,
                         "熔断后不得再执行（秒拒省火）")
        self.assertIn("断路器", res.outcomes[0])
        self.assertIn("未执行", res.outcomes[0])
        self.assertTrue(self.rec.has("tool-breaker card=dig event=trip"),
                        "trip 事件入账")
        self.assertTrue(self.rec.has("cooldown_s=900"),
                        "默认冷却 15min（rng 中点=零抖动）")

    def test_breaker_success_heals_streak(self):
        """成功治愈：2 败+1 成功+2 败不熔断（计数清零）。"""
        probe = Probe(results=[(1, "", "x"), (1, "", "x"), (0, "ok", ""),
                               (1, "", "x"), (1, "", "x"), (0, "ok", "")])
        ex = self.make(probe, goal_dir=self.gd)
        for t in range(1, 6):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        self.assertEqual(len(probe.calls), 5, "五次全执行（未熔断）")
        self.assertFalse(self.rec.has("event=trip"))

    def test_breaker_policy_denial_not_counted(self):
        """判定拦截类拒绝（err=未执行…）不计失败（llmpool no_failover 同型）。"""
        probe = Probe(default=(1, "", "未执行（判定拦截: scope 界外）"))
        ex = self.make(probe, goal_dir=self.gd)
        for t in range(1, 6):
            ex.execute([tool("curl", "https://a.shop.example/")],
                       "IN-0007", t)
        self.assertEqual(len(probe.calls), 5)
        self.assertFalse(self.rec.has("event=trip"),
                         "政策拒绝 5 连不得熔断卡")

    def test_breaker_cooldown_expires_lazily(self):
        """冷却窗过=惰性自动恢复：recover 事件+再次放行执行。"""
        probe = Probe(default=(1, "", "x"))
        clk = Clock()
        ex = self.make(probe, clock=clk, goal_dir=self.gd,
                       breaker_rng=lambda: 0.5)
        for t in (1, 2, 3):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 4)
        self.assertIn("断路器", res.outcomes[0])
        clk.advance(901.0)                      # 冷却窗（900s±20%·中点）过
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 5)
        self.assertEqual(len(probe.calls), 4, "冷却到期放行")
        self.assertTrue(self.rec.has("tool-breaker card=dig event=recover"))

    def test_breaker_state_persists_across_instances(self):
        """熔断状态落盘 goal 目录：新执行器实例仍熔断（重启不复活坏卡）。"""
        probe = Probe(default=(1, "", "x"))
        ex = self.make(probe, goal_dir=self.gd, breaker_rng=lambda: 0.5)
        for t in (1, 2, 3):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        self.assertTrue(os.path.exists(
            os.path.join(self.gd, "tool-breaker.json")))
        probe2 = Probe(default=(1, "", "x"))
        ex2 = self.make(probe2, goal_dir=self.gd)
        ex2.execute([tool("dig", "a.shop.example")], "IN-0008", 1)
        self.assertEqual(len(probe2.calls), 0, "重启后仍熔断（状态恢复）")

    def test_breaker_blocked_calls_do_not_extend_cooldown(self):
        """熔断期被拒调用不续冷却（拒≠败，不进计数）。"""
        probe = Probe(default=(1, "", "x"))
        clk = Clock()
        ex = self.make(probe, clock=clk, goal_dir=self.gd,
                       breaker_rng=lambda: 0.5)
        for t in (1, 2, 3):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 4)
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 5)
        clk.advance(901.0)
        ex.execute([tool("dig", "a.shop.example")], "IN-0007", 6)
        self.assertEqual(len(probe.calls), 4,
                         "两次被拒不延长冷却窗（原窗到期即放行）")

    # ---- 件a 异步 execution_id -------------------------------------------

    def test_long_task_returns_execution_id_promptly(self):
        """超阈长任务：发卡即回 execution_id，不占轮次不等结果。"""
        def slow(card, args):
            if card == "dig":
                time.sleep(0.4)
                return 0, "slow-done", ""
            return 0, "ok-out", ""            # 邻刀快=同步老路不受牵连
        ex = self.make(slow, goal_dir=self.gd, async_threshold_s=0.05)
        t0 = time.monotonic()
        res = ex.execute([tool("dig", "a.shop.example"),
                          tool("curl", "https://b.shop.example/")],
                         "IN-0007", 1)
        waited = time.monotonic() - t0
        self.assertLess(waited, 0.3,
                        "批屏障在阈后即收（不陪跑长任务）: %.2fs" % waited)
        self.assertEqual(len(res.outcomes), 2)
        self.assertIn("execution_id=", res.outcomes[0])
        self.assertEqual(res.outcomes[1], "tool curl rc=0 out=ok-out err=")
        self.assertTrue(self.rec.has("op=async-submit"),
                        "发卡事件入账（execution_id 可回放）")
        self.assertTrue(os.path.exists(
            os.path.join(self.gd, "tool-executions.tsv")),
            "状态行落 goal 目录")

    def test_async_completion_polled_and_reaped_next_turn(self):
        """结果轮询续接：poll 可查，下轮 execute 自动回填 outcome+事件。"""
        def slow(card, args):
            time.sleep(0.15)
            return 0, "slow-done", ""
        ex = self.make(slow, goal_dir=self.gd, async_threshold_s=0.03)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 1)
        m = re.search(r"execution_id=(\S+)", res.outcomes[0])
        self.assertIsNotNone(m, "outcome 带 execution_id")
        eid = m.group(1)
        deadline = time.monotonic() + 5.0
        snap = {}
        while time.monotonic() < deadline:
            snap = ex.poll_execution(eid)
            if snap.get("status") in ("completed", "failed"):
                break
            time.sleep(0.02)
        self.assertEqual(snap.get("status"), "completed")
        self.assertEqual(snap.get("rc"), 0)
        self.assertIn("slow-done", snap.get("out", ""))
        res2 = ex.execute([{"op": "note", "text": "下一轮"}], "IN-0007", 2)
        self.assertTrue(any("异步回填" in o and "slow-done" in o
                            for o in res2.outcomes),
                        "完成结果自动回填模型面: %r" % res2.outcomes)
        self.assertTrue(self.rec.has("op=async-result"),
                        "完成事件入账")

    def test_async_execution_id_deterministic(self):
        """同 intent/turn/call 位 → 同 execution_id（同输入同行为金样律）。"""
        def slow(card, args):
            time.sleep(0.2)
            return 0, "x", ""
        ex = self.make(slow, goal_dir=self.gd, async_threshold_s=0.03)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 3)
        m = re.search(r"execution_id=(\S+)", res.outcomes[0])
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "EX-IN-0007-t3-c0",
                         "execution_id=意图/轮/调用位确定性铸造")

    def test_short_task_sync_path_unchanged(self):
        """快于阈值：走同步老路，经典 outcome，零异步登记。"""
        def fast(card, args):
            return 0, "fast", ""
        ex = self.make(fast, goal_dir=self.gd, async_threshold_s=5.0)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 1)
        self.assertEqual(res.outcomes, ["tool dig rc=0 out=fast err="])
        self.assertFalse(self.rec.has("op=async-submit"))
        self.assertEqual(ex.pending_executions(), {})

    def test_async_failure_feeds_breaker(self):
        """异步失败回填时喂断路器：3 次异步败照样熔断（第 4 次秒拒）。"""
        def slow_fail(card, args):
            time.sleep(0.08)
            return 1, "", "async-boom"
        ex = self.make(slow_fail, goal_dir=self.gd,
                       async_threshold_s=0.02)
        for t in (1, 2, 3):
            ex.execute([tool("dig", "a.shop.example")], "IN-0007", t)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if all(p["status"] != "running"
                   for p in ex.pending_executions().values()):
                break
            time.sleep(0.02)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 4)
        self.assertEqual(len(res.outcomes), 4,
                         "三笔回填旧账+1笔新刀: %r" % res.outcomes)
        self.assertIn("断路器", res.outcomes[-1],
                      "三次异步失败（回填即报）应熔断第 4 刀: %r" % res.outcomes)

    def test_async_orphan_reconciled_on_reload(self):
        """孤儿对账：他进程遗留 running 状态行，新实例装载即标 orphaned。"""
        def slow(card, args):
            time.sleep(1.0)
            return 0, "x", ""
        ex = self.make(slow, goal_dir=self.gd, async_threshold_s=0.02)
        res = ex.execute([tool("dig", "a.shop.example")], "IN-0007", 1)
        eid = re.search(r"execution_id=(\S+)", res.outcomes[0]).group(1)
        ex2 = self.make(lambda c, a: (0, "y", ""), goal_dir=self.gd)
        snap = ex2.poll_execution(eid)
        self.assertEqual(snap.get("status"), "orphaned",
                         "旧 running 状态行=孤儿标记（不假完成不丢行）")


if __name__ == "__main__":
    unittest.main()
