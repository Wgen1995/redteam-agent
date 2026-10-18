# -*- coding: utf-8 -*-
"""功能24a·外部执行后端②c：local adapter=本地回环（TDD 红先行）。

本地回环=直接调我们自己的 warrior（进程内 WarriorLoop 全链真跑）：
- 证明抽象不漏：同一 Backend 接口/同一帧协议/同一归一通道，内部肌肉与
  外部肌肉同形（设计 §2「统一接口」的完备性由回环反证）；
- 测试主力：模型面=本地假模型服务（动态口），工具面=注入 spawn，时钟=
  FakeClock——零真子进程、零真外呼、零真实等待。
- supplement 落真通道=steer（warrior 原生定向轨）；interrupt 落真通道=
  steer.write_stop（stop 信号轨）——中途改目标/打断不新发明机制。

帧面：ready(runtime=graphled-warrior) → session(local:<warrior>:<task>) →
[tool_call/tool_result × 每 spawn] → text(战报摘要) → usage(transcript
聚合四维) → result(Report 状态映射)。

跑法：python3 -m unittest tests.test_backends_local -v
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
from backends import base, local  # noqa: E402

W = "warrior:LB-1"
TOOL = '{"op":"tool","card":"dig","args":["+short","A","shop.example"]}'
FACT = ('{"op":"ledger","cmd":"add-fact","args":{"intent-id":"INT-g1-0002",'
        '"kind":"info","target":"shop.example","detail":"面板 200","confidence":"0.7"}}')
DONE = '{"op":"done","reason":"探测完成"}'


class RecSpawn(object):
    """记录委托 argv 的假执行器（零真子进程）。"""

    def __init__(self):
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        return 0, "ok-out dig 应答", ""


class LocalCase(unittest.TestCase):
    def setUp(self):
        self.gd = shutil.copytree(FIX, tempfile.mkdtemp() + "/G-lb")
        self.addCleanup(shutil.rmtree, self.gd, ignore_errors=True)
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
        self.pool = llmpool_wire.attach(self.gd, env={})

    def _backend(self, **kw):
        args = dict(goal_dir=self.gd, battle_name="B-lb",
                    channels=[{"name": "m1", "model": "m1",
                               "base_url": self.srv.base, "api_key": "k"}],
                    pool=self.pool, warrior_id=W, max_intents=1,
                    max_turns=6, clock=self.clock, tool_spawn=self.spawn,
                    tool_state_path=self.state)
        args.update(kw)
        return local.LocalBackend(**args)

    def _opts(self, task_id="T-lb-1"):
        return base.ExecOptions(task_id=task_id, cwd=self.gd, prompt="任务包")

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    # --- ① 全链真跑 ------------------------------------------------------

    def test_full_chain_frames_and_ledger_writes(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": FACT},
                                     {"content": DONE}]})
        b = self._backend()
        seen = []
        s = b.execute(self._opts(),
                      on_event=lambda f, ss: seen.append(f["type"]))
        kinds = [f["type"] for f in s.frames]
        self.assertEqual(kinds[0], "ready")
        self.assertEqual(kinds[0:2], ["ready", "session"])
        self.assertIn("tool_call", kinds)
        self.assertIn("tool_result", kinds)
        # §7.2 序形：usage 紧邻 result 前；text=战报摘要夹其间
        self.assertEqual(kinds[-3:], ["usage", "text", "result"])
        # ready 帧标明 runtime=自有 warrior（本地回环身份）
        self.assertEqual(s.frames[0]["runtime"], "graphled-warrior")
        self.assertTrue(s.frames[1]["session_id"].startswith("local:"))
        # 工具帧来自真 spawn 包夹（name=卡名，arguments=参数表）
        tc = [f for f in s.frames if f["type"] == "tool_call"][0]
        self.assertEqual(tc["name"], "dig")
        self.assertEqual(json.loads(tc["arguments"]),
                         ["+short", "A", "shop.example"])
        tr = [f for f in s.frames if f["type"] == "tool_result"][0]
        self.assertEqual(tr["output"], "ok-out dig 应答")
        self.assertFalse(tr["is_error"])
        # 战果真落账（经既有执法链）：fact 行+done 状态+timeline 战报
        facts = Session(self.gd).rows("facts.tsv")
        self.assertTrue(any(r[4] == "面板 200" for r in facts))
        rows = [r for r in Session(self.gd).rows("intents.tsv")
                if r[0] == "INT-g1-0002"]
        self.assertEqual(rows[-1][3], "done")
        self.assertTrue(any(e.startswith("warrior-start") for e in
                            self._events()))
        # 终态与结果帧
        r = s.result()
        self.assertTrue(r.is_ok())
        self.assertTrue(s.terminal_observed())

    def test_usage_aggregated_from_transcripts_four_dims(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": FACT},
                                     {"content": DONE}]})
        s = self._backend().execute(self._opts())
        u = s.usage()
        # 三次模型调用 × stub 信封（prompt=100/completion=20）——transcript
        # 聚合面；cache 两维=战士无缓存账，诚实置 0
        self.assertEqual(u.input_tokens, 300)
        self.assertEqual(u.output_tokens, 60)
        self.assertEqual(u.cache_read_tokens, 0)
        self.assertEqual(u.cache_write_tokens, 0)
        uf = [f for f in s.frames if f["type"] == "usage"][0]
        self.assertEqual(uf["input_tokens"], 300)

    def test_tool_activity_watchdog_view(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": DONE}]})
        s = self._backend().execute(self._opts())
        self.assertEqual(s.tool_activity(),
                         {"calls": 1, "results": 1, "last_seq": 3})

    def test_result_error_mapping_on_budget_cap(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": DONE}]})
        s = self._backend(token_cap=1).execute(self._opts())
        # 帽=1：首轮记账后即触帽优雅停（既有 BudgetMeter 执法）
        r = s.result()
        self.assertEqual(r.status, "error")
        self.assertEqual(r.error["code"], "budget-cap")

    def test_capabilities_honest(self):
        b = self._backend()
        for cap in (base.CAP_SUPPLEMENT, base.CAP_INTERRUPT,
                    base.CAP_TOOL_ACTIVITY, base.CAP_TERMINAL_OBSERVED,
                    base.CAP_USAGE_TOKENS):
            self.assertTrue(b.capabilities.supports(cap), cap)
        for cap in (base.CAP_RESUME, base.CAP_COST_TICKS, base.CAP_MCP):
            self.assertFalse(b.capabilities.supports(cap), cap)

    # --- ② supplement/interrupt 落真通道（steer 轨） ---------------------

    def test_supplement_midrun_via_steer_reaches_model(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": DONE}]})
        b = self._backend()

        def on_ev(frame, session):
            if frame["type"] == "tool_call":
                session.supplement("改打 vpn 入口")
        s = b.execute(self._opts(), on_event=on_ev)
        # steer 行落 timeline（warrior 原生定向轨=回环同一条轨）
        self.assertTrue(any("warrior-steer target=%s text=改打 vpn 入口" % W
                            in e for e in self._events()))
        # 下一回合模型上下文真带上补充指令（中途改目标闭环）
        self.assertGreaterEqual(len(self.srv.requests), 2)
        self.assertIn("改打 vpn 入口",
                      json.dumps(self.srv.requests[-1], ensure_ascii=False))
        self.assertTrue(s.result().is_ok())

    def test_interrupt_midrun_via_stop_signal(self):
        self.srv.set_scripts({"m1": [{"content": TOOL}, {"content": DONE}]})
        b = self._backend()

        def on_ev(frame, session):
            if frame["type"] == "tool_call":
                session.interrupt_background_tools()
        s = b.execute(self._opts(), on_event=on_ev)
        r = s.result()
        self.assertEqual(r.status, "cancelled")     # stop-signal→cancelled
        self.assertTrue(any("warrior-stop warrior=%s" % W in e for e in
                            self._events()))
        # 打断后不再有第二次模型调用
        self.assertEqual(len(self.srv.requests), 1)

    def test_supplement_gated_for_other_sessions(self):
        s = base.Session(base.Capabilities())       # 无能力=拒（缺省安全失败）
        with self.assertRaises(base.CapabilityDenied):
            s.supplement("x")


if __name__ == "__main__":
    unittest.main()
