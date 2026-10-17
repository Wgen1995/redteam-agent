# -*- coding: utf-8 -*-
"""战士运行时·核心循环 E2E（W5 战士 MVP）。

全链：领意图(租约)→组上下文(R1)→llmpool 选道调模型→解析指令(协议)→
经 guard 执行工具(委托既有链零复制)/账本写命令→结果写账(facts/timeline/
transcript R4)→释放(done)→下一意图。模型面=本地假模型服务（动态口），
工具面=注入 spawn（不触网）。

跑法：python3 -m unittest tests.test_warrior_loop -v
"""
import json
import os
import shutil
import sys
import tempfile
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
from warrior import steer  # noqa: E402
from warrior.ledger_io import LedgerIO  # noqa: E402

W = "warrior:W-1"
TOOL = '{"op":"tool","card":"dig","args":["+short","A","shop.example"]}'
FACT = ('{"op":"ledger","cmd":"add-fact","args":{"intent-id":"INT-g1-0002",'
        '"kind":"info","target":"shop.example",'
        '"detail":"面板返回 200","confidence":"0.7"}}')
DONE = '{"op":"done","reason":"探测完成"}'


class RecSpawn(object):
    """记录委托 argv 的假执行器（可挂 hook 做回合间介入）。"""

    def __init__(self, hook=None):
        self.calls = []
        self.hook = hook

    def __call__(self, argv):
        self.calls.append(list(argv))
        if self.hook:
            self.hook(self)
        return 0, "ok-out dig 应答", ""


class LoopCase(unittest.TestCase):
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
        self.spawn = RecSpawn()

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _loop(self, scripts, **kw):
        self.srv.set_scripts(scripts)
        channels = [{"name": "m1", "model": "m1",
                     "base_url": self.srv.base, "api_key": "k"}]
        pool = llmpool_wire.attach(self.gd, env={})
        args = dict(goal_dir=self.gd, battle_name="B-x", channels=channels,
                    pool=pool, warrior_id=W, max_intents=3, max_turns=6,
                    lease_min=30, token_cap=100000, clock=self.clock,
                    tool_spawn=self.spawn, tool_state_path=self.state,
                    ctx_tokens=8000, heartbeat_min=5, stall_min=15)
        args.update(kw)
        return wloop.WarriorLoop(**args)

    def _latest(self, iid):
        rows = [r for r in Session(self.gd).rows("intents.tsv")
                if r[0] == iid]
        return rows[-1] if rows else None

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    def _requests_bodies(self):
        return self.srv.requests

    # --- ① 全链 ----------------------------------------------------------

    def test_full_chain_lease_think_exec_write_release(self):
        lp = self._loop({"m1": [{"content": TOOL}, {"content": FACT},
                                {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(rep.processed, 1)
        row = self._latest("INT-g1-0002")
        self.assertEqual(row[3], "done")
        # 工具经 guard 委托链恰一次
        self.assertEqual(len(self.spawn.calls), 1)
        self.assertEqual(self.spawn.calls[0][-4:], ["dig", "+short", "A",
                                                    "shop.example"])
        # 模型指令的账本写落行（intent-id 被战士覆写为持有意图）
        facts = Session(self.gd).rows("facts.tsv")
        self.assertTrue(any(r[4] == "面板返回 200" for r in facts))
        # 心跳/进展/停行入 timeline
        evs = self._events()
        self.assertTrue(any(e.startswith("warrior-start") for e in evs))
        self.assertTrue(any("warrior-progress" in e and "op=tool" in e
                            for e in evs))
        self.assertTrue(any(e.startswith("warrior-stop") for e in evs))
        # R4 transcript 落盘
        tp = os.path.join(self.gd, "transcripts", "INT-g1-0002.jsonl")
        with open(tp, encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        self.assertGreaterEqual(len(lines), 6)   # u/a ×3 轮
        # 预算计量入 budget.tsv（scope=意图）
        budget = Session(self.gd).rows("budget.tsv")
        self.assertTrue(all(r[5] == "INT-g1-0002" for r in budget[2:]))

    def test_malformed_outputs_tolerated_until_done(self):
        lp = self._loop({"m1": [{"content": "我先想想……"},
                                {"content": "```json\n{坏块}\n```"},
                                {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(self._latest("INT-g1-0002")[3], "done")
        self.assertEqual(len(self._requests_bodies()), 3,
                         "坏输出不改判 done 前须经受并继续")

    def test_dry_run_no_model_no_write(self):
        n_tl = len(read_rows(self.gd))
        lp = self._loop({"m1": [{"content": DONE}]})
        out = lp.dry_run()
        self.assertEqual(self._requests_bodies(), [], "dry-run 零模型调用")
        self.assertEqual(len(read_rows(self.gd)), n_tl, "dry-run 零账本写")
        self.assertEqual(self._latest("INT-g1-0002")[3], "pending",
                         "dry-run 不领意图")
        self.assertIn("admin 面板", out[0].text)

    # --- ② 让位与断点 ------------------------------------------------------

    def test_lease_stolen_mid_run_yields(self):
        def hook(sp):
            if len(sp.calls) == 1:      # 第一刀后：租约到期+他主接管
                self.clock.advance(60 * 31)
                LedgerIO(self.gd, "warrior:W-2").claim(
                    "INT-g1-0002", lease_min=30,
                    ts="2026-11-01T00:00:00Z")
        self.spawn.hook = hook
        lp = self._loop({"m1": [{"content": TOOL}, {"content": TOOL},
                                {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(len(self.spawn.calls), 1, "让位后不再执行")
        row = self._latest("INT-g1-0002")
        self.assertIn("[owner:warrior:W-2]", row[2])
        self.assertEqual(row[3], "active", "不与新主争夺状态迁移")
        self.assertTrue(any(e.startswith("warrior-yield") for e in
                            self._events()))

    def test_stall_exit_leases_intent_for_reclaim(self):
        def hook(sp):
            self.clock.advance(60 * 20)     # 超停滞窗 15min
        self.spawn.hook = hook
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]},
                        stall_min=15)
        rep = lp.run()
        self.assertEqual(rep.status, "stalled")
        self.assertTrue(any(e.startswith("warrior-stall") for e in
                            self._events()))
        self.assertEqual(self._latest("INT-g1-0002")[3], "active",
                         "停滞=交租约超时回收，不擅自状态迁移")

    def test_resume_rebuilds_context_from_timeline(self):
        # 首跑：一刀后停滞（intent 仍 active 归我）
        def hook(sp):
            self.clock.advance(60 * 20)
        self.spawn.hook = hook
        lp1 = self._loop({"m1": [{"content": TOOL}]}, stall_min=15)
        self.assertEqual(lp1.run().status, "stalled")
        # 重生：新循环实例（新脑），同意图续跑——resume 节取自 timeline
        self.clock.advance(1)
        self.spawn.hook = None
        lp2 = self._loop({"m1": [{"content": DONE}]})
        rep2 = lp2.run()
        self.assertEqual(rep2.status, "no-intents")
        self.assertEqual(self._latest("INT-g1-0002")[3], "done")
        msgs = json.dumps(self._requests_bodies()[-1]["messages"],
                          ensure_ascii=False)
        self.assertIn("warrior-progress", msgs, "断点续跑上下文带账本末行")

    # --- ③ 预算与停信号 ----------------------------------------------------

    def test_budget_cap_graceful_stop(self):
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]},
                        token_cap=100)   # 首调 usage=120 已越帽，二调前触
        rep = lp.run()
        self.assertEqual(rep.status, "budget-cap")
        self.assertEqual(len(self._requests_bodies()), 1)
        row = self._latest("INT-g1-0002")
        self.assertEqual(row[3], "blocked")
        self.assertIn("budget-cap", row[12])
        self.assertTrue(any("reason=budget-cap" in e for e in
                            self._events()))

    def test_stop_signal_graceful(self):
        def hook(sp):
            steer.write_stop(self.gd, W, reason="operator-halt",
                             ts="2026-02-02T02:40:00Z")
        self.spawn.hook = hook
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]})
        rep = lp.run()
        self.assertEqual(rep.status, "stop-signal")
        row = self._latest("INT-g1-0002")
        self.assertIn("stop-signal", row[12])

    def test_steer_injected_into_next_context(self):
        def hook(sp):
            steer.write_steer(self.gd, W, "优先 admin 面板",
                              ts="2026-02-02T02:40:00Z")
        self.spawn.hook = hook
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]})
        lp.run()
        msgs = json.dumps(self._requests_bodies()[-1]["messages"],
                          ensure_ascii=False)
        self.assertIn("优先 admin 面板", msgs)

    # --- ④ R2 串行链与界限 --------------------------------------------------

    def test_r2_serial_chain_dispatched_in_order(self):
        io = LedgerIO(self.gd, W)
        io.write("chain-create", {
            "engine": "web-blackbox", "kind": "recon", "origin": "llm",
            "budget-share": "100;5;0.5",
            "steps": "probe A|probe B|probe C",
            "timestamp": "2026-02-02T02:40:00Z"})
        rows = Session(self.gd).rows("intents.tsv")
        steps = {r[1]: r[0] for r in rows if r[1].startswith("probe")}
        io.write("set-intent-status", {"id": steps["probe A"],
                                       "status": "pending",
                                       "timestamp": "2026-02-02T02:40:00Z"})
        # 领走 fixture 意图（W-2 长租）——排除出本次 R2 断言面
        LedgerIO(self.gd, "warrior:W-2").claim(
            "INT-g1-0002", lease_min=240, ts="2026-02-02T02:40:00Z")
        lp = self._loop({"m1": [{"content": DONE}] * 3}, max_intents=5)
        rep = lp.run()
        self.assertEqual(rep.done_count, 3, "链三步全done")
        evs = self._events()
        act = [e for e in evs if "set-intent-status" in e and ":active" in e]
        dns = [e for e in evs if "set-intent-status" in e and ":done" in e]
        self.assertEqual(len(dns), 3)
        # 链序执法：probe A done 先于 probe B active（事件序）
        a_done = next(i for i, e in enumerate(evs)
                      if steps["probe A"] + ":done" in e)
        b_act = next(i for i, e in enumerate(evs)
                     if steps["probe B"] + ":active" in e)
        self.assertLess(a_done, b_act)

    def test_max_turns_bound_blocks_intent(self):
        lp = self._loop({"m1": [{"content": '{"op":"note","text":"还没想好"}'}
                              for _ in range(6)]}, max_turns=3)
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        row = self._latest("INT-g1-0002")
        self.assertEqual(row[3], "blocked")
        self.assertEqual(row[12], "max-turns")

    def test_time_window_exhaustion_stops(self):
        def hook(sp):
            self.clock.advance(60 * 60)
        self.spawn.hook = hook
        lp = self._loop({"m1": [{"content": TOOL}, {"content": DONE}]},
                        time_window_min=30, lease_min=120)  # 租约活过窗
        rep = lp.run()
        self.assertEqual(rep.status, "time-window")
        row = self._latest("INT-g1-0002")
        self.assertIn("time-window", row[12])


if __name__ == "__main__":
    unittest.main()
