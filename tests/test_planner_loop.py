# -*- coding: utf-8 -*-
"""功能5/8·补件二：常驻规划者 planner_loop（TDD 红测试先行）。

设计源：docs/design/2026-10-20-priority-planner-design.md 补件二——
  timeline 行追加=事件（轮询 epoch 增量）→ 防抖窗（默认 800ms，可配）→
  触发=态势研判（可达空格×排序公式→add_intent 走既有写入通道）；
  降级模式：收卡时惰性触发（规划者缺席合法）。
ARTEX 对照（plannerLoop 800ms debounce 同型）：它的事件=内存 notify 通道（丢了
就丢）；我们=账本行，可回放可验真（实时=回放特例律）。

Ruling（写测试即写契约）：
- R-PLN-1 事件源=change_token(epoch, timeline.tsv mtime_ns, size)：epoch 抓
  append_tl_locked 追加路径（.timeline.epoch 递增），mtime/size 兜住 Ctx.commit
  整表重写路径（写命令不递增 epoch）——两类写方都在账本上，令牌必变。
- R-PLN-2 只派可达空格（P3 可达先行律公式化）：排序覆盖全部空格（不可达
  reach=0.3 只降序不派活），add-intent 恰达 max_adds 张。
- R-PLN-3 派活走 registry.lookup("add-intent")（goal 写锁包装既有执法链），
  不直接改 write_cmds；dedup_key（-+matrix-test+planner: 面 × 类）机械判重
  =研判幂等；priority=五因子加权分（K1 通道回填）；detail 落五因子明细
  （可解释律）。
- R-PLN-4 防抖=ARTEX 形：首见变更起表（pending_since），窗内后续变更合并
  （drain），now-pending_since≥窗长才触发；自写并回基线防自触发。
- R-PLN-5 降级模式：lazy_trigger(goal_dir, ts) 无循环实例单发一轮（sweep+
  研判），与常驻轮同效——规划者缺席合法，不缺席才自动。

跑法：python3 -m unittest tests.test_planner_loop -v
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from ledger import registry  # noqa: E402
from ledger import planner_loop as PL  # noqa: E402
from ledger.core import Session, write_tsv, TABLES  # noqa: E402
from ledger import timeline as TL  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-20T10:00:00Z"
_IT = TABLES["intents.tsv"].index("title")
_IP = TABLES["intents.tsv"].index("priority")
_IS = TABLES["intents.tsv"].index("status")
_IK = TABLES["intents.tsv"].index("kind")

ASSETS = [
    ["AST-0001", "root-domain", "shop.example", "", "1", "2", ""],
    ["AST-0002", "subdomain", "admin.shop.example", "", "1", "2", ""],
    ["AST-0003", "subdomain", "vpn.shop.example", "", "1", "2", ""],
]
EDGES = [
    ["E-0001", "parent", "AST-0001", "AST-0002", "planner-loop-fixture", "2", ""],
]
MATRIX = [
    ["admin.shop.example", "inj.sql", "", "", "", "2", "", ""],
    ["admin.shop.example", "wstg-inpv", "", "", "", "2", "", ""],
    ["vpn.shop.example", "wstg-inpv", "", "", "", "2", "", ""],
]
CREDS = [
    ["CRED-0001", "password", "admin", "u1", "{{vault:cred-1}}", "AST-0002",
     "", "", "", "", "active", "", "", "2", "", ""],
]
FACTS = [
    ["F-0001", "INT-g1-0001", "info", "admin.shop.example", "新鲜线索", "0.9",
     "2", "2026-10-20T09:00:00Z"],
]


def _mkgoal(tmp, name="G-t"):
    gd = shutil.copytree(FIX, os.path.join(tmp, name))
    for tname, rows in (("assets.tsv", ASSETS), ("edges.tsv", EDGES),
                        ("matrix.tsv", MATRIX), ("creds.tsv", CREDS),
                        ("facts.tsv", FACTS)):
        write_tsv(os.path.join(gd, tname), [list(r) for r in rows])
    return gd


class FakeClock(object):
    """单调钟+睡眠注入：sleep 即推进（零真实等待，测试确定性）。"""

    def __init__(self, t=1000.0):
        self.t = t

    def mono(self):
        return self.t

    def sleep(self, s):
        self.t += max(0.0, s)


def _intent_rows(gd):
    return Session(gd).rows("intents.tsv")


def _planner_titles(gd):
    return sorted(r[_IT] for r in _intent_rows(gd)
                  if r[_IT].startswith("planner: "))


class TestChangeToken(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def test_token_moves_on_append_path(self):
        t0 = PL.change_token(self.gd)
        TL.append_tl_locked(self.gd, TS, "planner-测试事件", "bench", "P3")
        self.assertNotEqual(PL.change_token(self.gd), t0,
                            "append_tl_locked 追加须动令牌（epoch 递增）")

    def test_token_moves_on_whole_rewrite_path(self):
        """写命令（Ctx.commit 整表重写）不递增 epoch——mtime/size 兜住（R-PLN-1）。"""
        t0 = PL.change_token(self.gd)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = registry.lookup("add-fact")(
                self.gd, ["--intent-id=INT-g1-0001", "--kind=info",
                          "--target=shop.example", "--detail=轮询测试",
                          "--confidence=0.9", "--timestamp=" + TS])
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertNotEqual(PL.change_token(self.gd), t0,
                            "整表重写路径（写命令）也须动令牌")


class TestShouldFire(unittest.TestCase):
    def test_debounce_boundary(self):
        self.assertFalse(PL.should_fire(None, 999.0, 800))
        self.assertFalse(PL.should_fire(0.0, 0.7999, 800))
        self.assertTrue(PL.should_fire(0.0, 0.8, 800))
        self.assertTrue(PL.should_fire(0.0, 5.0, 800))
        self.assertTrue(PL.should_fire(0.0, 0.2, 100))


class TestDebounceLoop(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)
        self.clock = FakeClock()
        # poll_interval=0.1 < 防抖窗 0.8：poll 间钟推进小于窗长，可测窗内不触发
        self.loop = PL.PlannerLoop(self.gd, ts_fn=lambda: TS,
                                   mono=self.clock.mono, sleep=self.clock.sleep,
                                   debounce_ms=800, poll_interval=0.1)

    def _event(self):
        TL.append_tl_locked(self.gd, TS, "planner-轮询事件-%d"
                            % len(_intent_rows(self.gd)), "bench", "P3")

    def test_no_event_no_fire(self):
        for _ in range(5):
            self.assertEqual(self.loop.poll(), "idle")
        self.assertEqual(self.loop.rounds, 0)

    def test_no_fire_before_window_elapses(self):
        self._event()
        self.assertEqual(self.loop.poll(), "pending")
        self.clock.t += 0.5            # 累计 0.6s：窗内不触发
        self.assertEqual(self.loop.poll(), "pending")
        self.assertEqual(self.loop.rounds, 0)

    def test_bursts_merge_into_single_round(self):
        self._event()
        self.assertEqual(self.loop.poll(), "pending")
        self._event()                   # 窗内第二事件=合并（drain）
        self._event()
        self.clock.t += 1.0             # 过窗
        self.assertEqual(self.loop.poll(), "fired")
        self.assertEqual(self.loop.rounds, 1, "突发合并=恰一轮")
        self.assertEqual(self.loop.poll(), "idle", "自写回基线，不自触发")
        self.assertEqual(self.loop.rounds, 1)

    def test_rearm_after_fire(self):
        self._event()
        self.loop.poll()
        self.clock.t += 1.0
        self.assertEqual(self.loop.poll(), "fired")
        self._event()
        self.assertEqual(self.loop.poll(), "pending", "触发后可重新武装")
        self.clock.t += 1.0
        self.assertEqual(self.loop.poll(), "fired")
        self.assertEqual(self.loop.rounds, 2)


class TestAssessRound(unittest.TestCase):
    """态势研判轮：可达空格×排序公式→add_intent（既有通道，R-PLN-2/3）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def test_lazy_trigger_adds_reachable_gaps_only(self):
        added = PL.lazy_trigger(self.gd, TS)
        titles = _planner_titles(self.gd)
        self.assertEqual(
            titles,
            sorted(["planner: admin.shop.example × wstg-inpv",
                    "planner: admin.shop.example × inj.sql"]),
            "只派可达空格（vpn=不可达不派，R-PLN-2）")
        self.assertEqual(len(added), 2)
        rows = {r[_IT]: r for r in _intent_rows(self.gd)}
        row = rows["planner: admin.shop.example × wstg-inpv"]
        self.assertEqual(row[_IP], "0.9000", "priority=五因子加权分（K1 回填）")
        self.assertEqual(row[_IK], "matrix-test")
        self.assertIn("reachability=1.0000",
                    row[TABLES["intents.tsv"].index("detail")],
                    "detail 落五因子明细（可解释律）")
        self.assertEqual(row[_IS], "candidate",
                         "origin=adjacency 非直达 pending（晋升走既有打分通道）")

    def test_second_round_idempotent(self):
        PL.lazy_trigger(self.gd, TS)
        added2 = PL.lazy_trigger(self.gd, TS)
        self.assertEqual(added2, [], "dedup_key 机械判重=研判幂等")
        self.assertEqual(len(_planner_titles(self.gd)), 2)

    def test_round_runs_replacer_sweep(self):
        """降级单发轮含重派扫面（补件三消费者接线；blocked 卡被重派器收口）。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = registry.lookup("add-intent")(
                self.gd, ["--title=断线卡", "--engine=web-blackbox",
                          "--kind=recon", "--origin=recon-event",
                          "--budget-share=1;1;1", "--timestamp=" + TS])
            rc2 = registry.lookup("set-intent-status")(
                self.gd, ["--id=" + [r[0] for r in _intent_rows(self.gd)
                                     if r[_IT] == "断线卡"][-1],
                          "--status=active", "--timestamp=" + TS])
            rc3 = registry.lookup("set-intent-status")(
                self.gd, ["--id=" + [r[0] for r in _intent_rows(self.gd)
                                     if r[_IT] == "断线卡"][-1],
                          "--status=blocked",
                          "--reason=transport-fault: 断", "--timestamp=" + TS])
        self.assertTrue(rc == rc2 == rc3 == 0, buf.getvalue())
        PL.lazy_trigger(self.gd, TS)
        rows = [r for r in _intent_rows(self.gd) if r[_IT] == "断线卡"]
        self.assertEqual(rows[-1][_IS], "active",
                         "研判轮内嵌重派扫面：纯故障卡已重入池")

    def test_no_gaps_no_writes(self):
        write_tsv(os.path.join(self.gd, "matrix.tsv"), [
            ["admin.shop.example", "inj.sql", "x", "全覆盖", "", "2", TS, ""]])
        before = len(Session(self.gd).rows("timeline.tsv"))
        self.assertEqual(PL.lazy_trigger(self.gd, TS), [])
        self.assertEqual(len(Session(self.gd).rows("timeline.tsv")), before,
                         "无空格=零写入")

    def test_debounce_from_config_file(self):
        with open(os.path.join(self.gd, "planner.json"), "w",
                  encoding="utf-8") as f:
            f.write('{"debounce_ms": 50, "max_adds": 1}')
        clock = FakeClock()
        loop = PL.PlannerLoop(self.gd, ts_fn=lambda: TS,
                              mono=clock.mono, sleep=clock.sleep)
        self.assertEqual(loop.debounce_ms, 50)
        self.assertEqual(loop.max_adds, 1)
        TL.append_tl_locked(self.gd, TS, "配置轮询", "bench", "P3")
        self.assertEqual(loop.poll(), "pending")
        clock.t += 0.1
        self.assertEqual(loop.poll(), "fired")
        self.assertEqual(len(_planner_titles(self.gd)), 1,
                         "max_adds=1 限流（防一轮倾倒）")


class TestEndToEnd(unittest.TestCase):
    def test_event_to_intent_closed_loop(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        gd = _mkgoal(self._tmp.name)
        clock = FakeClock()
        loop = PL.PlannerLoop(gd, ts_fn=lambda: TS, mono=clock.mono,
                              sleep=clock.sleep, poll_interval=1.0)
        TL.append_tl_locked(gd, TS, "战士写回: 新线索出现", "warrior:W-1", "P3")
        states = [loop.poll() for _ in range(4)]
        self.assertIn("fired", states, "事件→防抖→研判闭环必须点火")
        titles = _planner_titles(gd)
        self.assertEqual(len(titles), 2, "新活自动入池（几十秒内→测试即时）")
        evs = [r[TABLES["timeline.tsv"].index("event")]
               for r in Session(gd).rows("timeline.tsv")]
        self.assertTrue(any(e.startswith("add-intent INT-") for e in evs),
                        "派活经既有 add-intent 通道（timeline 全审计）")


if __name__ == "__main__":
    unittest.main()
