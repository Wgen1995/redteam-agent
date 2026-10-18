# -*- coding: utf-8 -*-
"""战士同轮工具并行（E 舰吸收件③）——cyber-harness loop.go:498 语义对齐。

对齐档（docs/reviews/2026-10-19-E-cyberharness-全件对齐.md E3/N2）三律+
依赖律逐条钉测（假模型服务+假工具执行面，零真外呼）：
  律① 同轮无依赖 tool 并行（信号量上限 16，defaults.go:15 同源）；
  律② 并行执行、串行入账——账本写保持派发原序（哈希链不乱）；
  律③ 完成序与派发序解耦——结果按调用 id（派发序号）归位；
  律④ 保守依赖检测——同卡同目标串行（同资产读写不并行）；
  附则 截断响应不执行工具（对齐档 E3 引文）。

跑法：python3 -m unittest tests.test_warrior_parallel_tools -v
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import llmpool_wire  # noqa: E402
from ledger.core import Session  # noqa: E402
from ledger.timeline import read_rows  # noqa: E402
from tests.test_warrior_fake_model import FakeClock, FakeModelServer  # noqa: E402
from tools import install as tool_install  # noqa: E402
from warrior import loop as wloop  # noqa: E402

W = "warrior:W-1"
DONE = '{"op":"done","reason":"并行批收官"}'


def tool(card, *args):
    return {"op": "tool", "card": card, "args": list(args)}


def fact(detail):
    return {"op": "ledger", "cmd": "add-fact",
            "args": {"kind": "info", "target": "shop.shop.example",
                     "detail": detail, "confidence": "0.7"}}


def fence(*objs):
    """多指令一回：逐个 json 围栏块（协议同形，序=派发序）。"""
    return "\n".join("```json\n%s\n```" % json.dumps(
        o, ensure_ascii=False) for o in objs)


class ProbeSpawn(object):
    """可编程假工具执行面：按 argv 子串挂规则（延迟/等屏障/发屏障），
    记录起止单调钟、起始/完成序、并发峰值——并行律断言探针。"""

    def __init__(self):
        self._lock = threading.Lock()
        self.calls = []            # argv 副本（起跑序）
        self.spans = []            # (joined, start, end) 单调钟
        self.started_order = []
        self.finished_order = []
        self.active = 0
        self.max_active = 0
        self.wait_results = []     # wait_for 屏障的成活记录（False=超时=未重叠）
        self.rules = {}            # argv 子串 -> 规则 dict

    def __call__(self, argv):
        joined = " ".join(str(a) for a in argv)
        rule = next((r for pat, r in sorted(self.rules.items())
                     if pat in joined), None)
        with self._lock:
            self.calls.append(list(argv))
            self.started_order.append(joined)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            t0 = time.monotonic()
        if rule:
            for ev in rule.get("set_on_start", []):
                ev.set()
            if rule.get("sleep"):
                time.sleep(rule["sleep"])
            ev = rule.get("wait_for")
            if ev is not None:
                self.wait_results.append(bool(ev.wait(timeout=5.0)))
        with self._lock:
            self.active -= 1
            t1 = time.monotonic()
            self.finished_order.append(joined)
            self.spans.append((joined, t0, t1))
        if rule:
            return rule.get("rc", 0), rule.get("out", "ok-out"), ""
        return 0, "ok-out", ""

    def span_of(self, token):
        return [s for s in self.spans
                if (" " + token + " ") in (" " + s[0] + " ")]

    def finished_idx(self, marker):
        for i, j in enumerate(self.finished_order):
            if marker in j:
                return i
        return -1


class ParallelCase(unittest.TestCase):
    """E2E：假模型一回多指令 → WarriorLoop 全链（真账本/真协议面）。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.state = os.path.join(self.gd, "..",
                                  os.path.basename(self.gd) + "-cards.tsv")
        for n in ("curl", "dig"):
            ok, why = tool_install.install(n, "2026-10-18T10:00:00Z",
                                           state_path=self.state)
            self.assertTrue(ok, why)
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)
        self.clock = FakeClock(start=1770000000.0)
        self.probe = ProbeSpawn()
        self.addCleanup(shutil.rmtree, self.gd)

    def _loop(self, scripts, **kw):
        self.srv.set_scripts(scripts)
        channels = [{"name": "m1", "model": "m1",
                     "base_url": self.srv.base, "api_key": "k"}]
        pool = llmpool_wire.attach(self.gd, env={})
        args = dict(goal_dir=self.gd, battle_name="B-x", channels=channels,
                    pool=pool, warrior_id=W, max_intents=3, max_turns=6,
                    lease_min=30, token_cap=100000, clock=self.clock,
                    tool_spawn=self.probe, tool_state_path=self.state,
                    ctx_tokens=8000, heartbeat_min=5, stall_min=15)
        args.update(kw)
        return wloop.WarriorLoop(**args)

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    def _tool_calls(self):
        """op=tool 事件的 call= id 序（派发原序入账面）。无 call= 记 -1。"""
        out = []
        for e in self._events():
            if "op=tool" not in e:
                continue
            parts = e.split("call=")
            out.append(int(parts[1]) if len(parts) > 1 else -1)
        return out

    def _results_msg(self):
        for m in reversed(self.srv.requests[-1]["messages"]):
            if m["role"] == "user" and "指令结果" in m["content"]:
                return m["content"]
        return ""

    def _assert_chain_intact(self):
        from ledger import core as lcore
        from ledger.schemas import TABLES
        cols = TABLES["timeline.tsv"]
        hi, pi = cols.index("hash"), cols.index("prev_hash")
        prev = lcore.GENESIS
        for r in Session(self.gd).rows("timeline.tsv"):
            self.assertEqual(r[pi], prev, "timeline 哈希链 prev 断裂")
            prev = r[hi]

    # --- 律①：同轮无依赖并行 --------------------------------------------

    def test_distinct_tools_overlap_in_same_turn(self):
        # 双向会合证并行：两刀各自「起跑即发栅栏+等对方栅栏」——串行必超时
        ea, eb = threading.Event(), threading.Event()
        self.probe.rules["t1.shop.example"] = {"set_on_start": [ea],
                                          "wait_for": eb}
        self.probe.rules["t2.shop.example"] = {"set_on_start": [eb],
                                          "wait_for": ea}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              tool("curl", "-sS", "https://t2.shop.example/"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 2)
        self.assertEqual(self.probe.wait_results, [True, True],
                         "律①：同轮无依赖工具须重叠（双向会合全成活）")

    def test_same_tool_distinct_targets_overlap(self):
        ea, eb = threading.Event(), threading.Event()
        self.probe.rules["a.shop.example"] = {"set_on_start": [ea],
                                         "wait_for": eb}
        self.probe.rules["b.shop.example"] = {"set_on_start": [eb],
                                         "wait_for": ea}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "a.shop.example"),
                              tool("dig", "+short", "A", "b.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 2)
        self.assertEqual(self.probe.wait_results, [True, True],
                         "律①/④：同卡异目标须并行（双向会合全成活）")

    def test_semaphore_caps_at_sixteen(self):
        self.probe.rules["example"] = {"sleep": 0.2}
        calls = [tool("dig", "+short", "A", "t%02d.shop.example" % i)
                 for i in range(20)]
        lp = self._loop({"m1": [{"content": fence(*calls)},
                                {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 20)
        self.assertEqual(self.probe.max_active, 16,
                         "律①：信号量上限 16（实测峰值 %d）"
                         % self.probe.max_active)

    def test_max_parallel_tools_configurable(self):
        self.probe.rules["example"] = {"sleep": 0.08}
        calls = [tool("dig", "+short", "A", "t%02d.shop.example" % i)
                 for i in range(6)]
        lp = self._loop({"m1": [{"content": fence(*calls)},
                                {"content": DONE}]},
                        max_parallel_tools=2)
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self.probe.max_active, 2,
                         "并行上限可配（实测峰值 %d）"
                         % self.probe.max_active)

    def test_parallel_batch_wall_time_beats_serial(self):
        self.probe.rules["t1.shop.example"] = {"sleep": 0.25}
        self.probe.rules["t2.shop.example"] = {"sleep": 0.25}
        self.probe.rules["t3.shop.example"] = {"sleep": 0.25}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              tool("curl", "-sS", "https://t2.shop.example/"),
                              tool("dig", "+short", "MX", "t3.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        starts = [s[1] for s in self.probe.spans]
        ends = [s[2] for s in self.probe.spans]
        wall = max(ends) - min(starts)
        self.assertLess(wall, 0.55, "三刀 0.25s 并行批墙钟须<0.55s（实测 "
                                    "%.2fs=串行）" % wall)

    # --- 律③：完成序解耦，结果按调用 id 归位 ------------------------------

    def test_results_in_dispatch_order_despite_reversed_completion(self):
        self.probe.rules["t1.shop.example"] = {"sleep": 0.30, "out": "out-t1"}
        self.probe.rules["t2.shop.example"] = {"sleep": 0.02, "out": "out-t2"}
        self.probe.rules["t3.shop.example"] = {"sleep": 0.12, "out": "out-t3"}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              tool("curl", "-sS", "https://t2.shop.example/"),
                              tool("dig", "+short", "MX", "t3.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        # 完成序确已倒置：t2 → t3 → t1
        self.assertLess(self.probe.finished_idx("t2.shop.example"),
                        self.probe.finished_idx("t3.shop.example"))
        self.assertLess(self.probe.finished_idx("t3.shop.example"),
                        self.probe.finished_idx("t1.shop.example"))
        # 模型收到的指令结果面=派发序 t1 → t2 → t3
        msg = self._results_msg()
        self.assertLess(msg.index("out-t1"), msg.index("out-t2"))
        self.assertLess(msg.index("out-t2"), msg.index("out-t3"))
        # 入账面 call= id 派发原序
        self.assertEqual(self._tool_calls(), [0, 1, 2])

    # --- 律②：并行执行、串行入账（原序+哈希链） ---------------------------

    def test_ledger_writes_original_order_and_chain_intact(self):
        self.probe.rules["t1.shop.example"] = {"sleep": 0.15}
        self.probe.rules["t2.shop.example"] = {"sleep": 0.15}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              fact("并行事实一"),
                              tool("curl", "-sS", "https://t2.shop.example/"),
                              fact("并行事实二"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        evs = self._events()

        led_pos = [i for i, e in enumerate(evs) if "op=ledger" in e]
        p_tool0 = next(i for i, e in enumerate(evs)
                       if "op=tool" in e and "call=0" in e)
        p_tool2 = next(i for i, e in enumerate(evs)
                       if "op=tool" in e and "call=2" in e)
        self.assertEqual(self._tool_calls(), [0, 2])
        self.assertEqual(len(led_pos), 2)
        self.assertLess(p_tool0, led_pos[0], "律②：账写落在前刀批收拢后")
        self.assertLess(led_pos[0], p_tool2)
        self.assertLess(p_tool2, led_pos[1])
        facts = Session(self.gd).rows("facts.tsv")
        details = [r[4] for r in facts]
        self.assertLess(details.index("并行事实一"),
                        details.index("并行事实二"), "账本写保持派发原序")
        self._assert_chain_intact()

    # --- 律④：同卡同目标串行 ----------------------------------------------

    def test_same_tool_same_target_never_overlaps(self):
        self.probe.rules["t1.shop.example"] = {"sleep": 0.25}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              tool("dig", "+short", "MX", "t1.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 2)
        s = sorted(self.probe.span_of("dig"), key=lambda x: x[1])
        self.assertGreaterEqual(s[1][1], s[0][2],
                                "律④：同卡同目标（同资产读写）不得重叠")

    # --- 语义保真：串行面不变量 -------------------------------------------

    def test_single_tool_turn_semantics_unchanged(self):
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "shop.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 1)
        self.assertEqual(self.probe.calls[0][-4:],
                         ["dig", "+short", "A", "shop.shop.example"])
        self.assertIn("tool dig rc=0 out=ok-out err=",
                      self._results_msg(), "单刀回合 summary 面不变")
        self.assertTrue(any("op=tool" in e and "card=dig" in e
                            and "rc=0" in e and "call=0" in e
                            for e in self._events()))

    def test_done_terminates_rest_of_batch(self):
        self.probe.rules["example"] = {"sleep": 0.05}
        lp = self._loop({"m1": [
            {"content": fence(tool("dig", "+short", "A", "t1.shop.example"),
                              {"op": "done", "reason": "中途收官"},
                              tool("curl", "-sS", "https://t2.shop.example/"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 1, "done 后同批余刀不执行")
        rows = [r for r in Session(self.gd).rows("intents.tsv")
                if r[0] == "INT-g1-0002"]
        self.assertEqual(rows[-1][3], "done")

    def test_truncated_reply_executes_no_tools(self):
        raw = json.dumps({
            "choices": [{"message": {"role": "assistant",
                                     "content": fence(
                                         tool("dig", "+short", "A",
                                              "t1.shop.example"))},
                         "finish_reason": "length"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20}},
            ensure_ascii=False).encode("utf-8")
        lp = self._loop({"m1": [{"raw_body": raw}, {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self.probe.calls, [],
                         "附则：截断响应不得执行工具")

    def test_outcomes_include_note_and_ledger_in_order(self):
        self.probe.rules["t1.shop.example"] = {"out": "mark-t1"}
        self.probe.rules["t2.shop.example"] = {"out": "mark-t2"}
        self.probe.rules["t3.shop.example"] = {"out": "mark-t3"}
        lp = self._loop({"m1": [
            {"content": fence(
                tool("dig", "+short", "A", "t1.shop.example"),
                {"op": "note", "text": "留个脚印"},
                tool("curl", "-sS", "https://t2.shop.example/"),
                fact("混合批事实"),
                tool("dig", "+short", "MX", "t3.shop.example"))},
            {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(len(self.probe.calls), 3)
        msg = self._results_msg()
        self.assertLess(msg.index("mark-t1"), msg.index("留个脚印"))
        self.assertLess(msg.index("留个脚印"), msg.index("mark-t2"))
        self.assertLess(msg.index("mark-t2"), msg.index("ledger add-fact"))
        self.assertLess(msg.index("ledger add-fact"), msg.index("mark-t3"))
        self.assertEqual(self._tool_calls(), [0, 2, 4])


class ExecutorCase(unittest.TestCase):
    """单元：ToolBatchExecutor 端口直挂假件（无模型无账本）。"""

    @classmethod
    def setUpClass(cls):
        from warrior import executor as wexec
        cls.wexec = wexec

    def setUp(self):
        self.tl = []
        self.ledger_marks = []

    def _mk(self, tool_exec, max_parallel=16):
        def ledger_write(cmd, args):
            self.ledger_marks.append((cmd, time.monotonic()))
            return 0, "ledger-ok"
        return self.wexec.ToolBatchExecutor(
            tool_exec=tool_exec, ledger_write=ledger_write,
            now=lambda: 1770000000.0, ts=lambda: "2026-02-02T02:40:00Z",
            add_tl=lambda e, ts: self.tl.append(e),
            warrior_id=W, max_parallel=max_parallel)

    def test_dep_key_conservative_target_extraction(self):
        target_of, dep_key = self.wexec.target_of, self.wexec.dep_key
        # 同卡同目标不同旗标=同键（律④）
        self.assertEqual(dep_key("dig", ["+short", "A", "shop.shop.example"]),
                         dep_key("dig", ["+short", "MX", "shop.shop.example"]))
        # 异目标=异键（可并行）
        self.assertNotEqual(dep_key("dig", ["+short", "A", "a.shop.example"]),
                            dep_key("dig", ["+short", "A", "b.shop.example"]))
        # 异卡同目标=异键（保守域=同卡）
        self.assertNotEqual(dep_key("dig", ["A", "a.shop.example"]),
                            dep_key("curl", ["-sS", "a.shop.example"]))
        # 目标相=末位起首个含 ./： 的非旗标（httpx 形：旗标值在目标后）
        self.assertEqual(target_of(["-u", "https://x.shop.example", "-rate",
                                    "20", "-silent"]),
                         "https://x.shop.example")
        # 无目标相=同卡全串行（保守失败方向）
        self.assertEqual(dep_key("kubectl", ["--context", "eng", "get",
                                             "pods"]),
                         dep_key("kubectl", ["get", "pods"]))

    def test_results_placed_by_call_id_not_completion(self):
        gate = threading.Event()
        finished = []

        def fx(card, args):
            if card == "slowA":
                self.assertTrue(gate.wait(timeout=5.0),
                                "快刀须先于慢刀完成")
            finished.append(card)
            if card == "fastB":
                gate.set()
            return 0, "r-" + card, ""
        ex = self._mk(fx)
        res = ex.execute([tool("slowA", "x.shop.example"),
                          tool("fastB", "y.shop.example")], "INT-x", 1)
        self.assertEqual(finished, ["fastB", "slowA"], "完成序确已倒置")
        self.assertTrue(res.outcomes[0].startswith("tool slowA rc=0"),
                        "律③：结果按调用 id 归位（0 号槽=slowA）")
        self.assertTrue(res.outcomes[1].startswith("tool fastB rc=0"))
        calls = [int(e.split("call=")[1]) for e in self.tl
                 if "call=" in e]
        self.assertEqual(calls, [0, 1], "入账面按派发原序")

    def test_ledger_barrier_and_serial_write_order(self):
        marks = []

        def fx(card, args):
            time.sleep(0.2)
            marks.append(("tool-end", time.monotonic()))
            return 0, "o", ""
        ex = self._mk(fx)
        ex.execute([tool("dig", "a.shop.example"), fact("先"), fact("后")],
                   "INT-x", 1)
        tool_end = marks[0][1]
        self.assertGreaterEqual(self.ledger_marks[0][1], tool_end,
                                "律②：账写=批次屏障，等在飞刀收拢")
        self.assertLessEqual(self.ledger_marks[0][1],
                             self.ledger_marks[1][1], "账写原序不倒")

    def test_tool_exception_isolated_in_batch(self):
        def fx(card, args):
            if card == "boom":
                raise RuntimeError("guard 通道炸了")
            return 0, "fine", ""
        ex = self._mk(fx)
        res = ex.execute([tool("boom", "a.shop.example"),
                          tool("ok", "b.shop.example")], "INT-x", 1)
        self.assertIn("rc=2", res.outcomes[0])
        self.assertIn("tool 通道异常", res.outcomes[0])
        self.assertIn("tool ok rc=0", res.outcomes[1], "同批邻刀不受牵连")

    def test_semaphore_unit_bounds_concurrency(self):
        lock = threading.Lock()
        st = {"active": 0, "max": 0}

        def fx(card, args):
            with lock:
                st["active"] += 1
                st["max"] = max(st["max"], st["active"])
            time.sleep(0.06)
            with lock:
                st["active"] -= 1
            return 0, "", ""
        ex = self._mk(fx, max_parallel=3)
        ex.execute([tool("c%d" % i, "t%d.shop.example" % i) for i in range(10)],
                   "INT-x", 1)
        self.assertEqual(st["max"], 3, "信号量=可配上限执法")

    def test_done_and_note_semantics_preserved(self):
        seen = []

        def fx(card, args):
            seen.append(card)
            return 0, "o", ""
        ex = self._mk(fx)
        res = ex.execute([{"op": "note", "text": "先留言"},
                          tool("dig", "a.shop.example"),
                          {"op": "done", "reason": "够了"},
                          tool("curl", "b.shop.example")], "INT-x", 1)
        self.assertTrue(res.saw_done)
        self.assertEqual(res.done_reason, "够了")
        self.assertEqual(seen, ["dig"], "done 后余刀不执行")
        self.assertTrue(res.outcomes[0].startswith("note: 先留言"))
        self.assertTrue(res.outcomes[1].startswith("tool dig rc=0"))


if __name__ == "__main__":
    unittest.main()
