# -*- coding: utf-8 -*-
"""loop 接线测试（修复舰落舱后总控接线·TDD 红先行）。

四线（各纯函数模块头注接线位 → cli/warrior/loop.py 接线）：
  ① repair        —— run() 落 warrior-start 行后 plan_repair：plan 非空→
                      add_tl 合成收尾事件 + 状态行按池 _persist 同律原子重写；
  ② compaction    —— process_intent 每 turn ctx.build 后 needs_compaction→
                      build_compaction（summarizer=None 确定性抽取）产包替换
                      被遮蔽素材；
  ③ resume_driver —— run() 重生入口 build_resume_directive：resume→prompt
                      注入 steers；round-limit→_stop 判死不再重生；
  ④ corps         —— __init__ 装配 load_corps + 领单后 resolve 出 skill_path
                      进简报 + tool/ledger 指令前置 authorize 拒=rc1+reason。

金样律：既有 loop/context/warrior 族测试零改动全绿；本件只测接线行为
（每线≥2：正路径+幂等/降级）。零端口：模型面=进程内假客户端（无 HTTP）。

跑法：python3 -m unittest tests.test_warrior_loop_wiring -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger.core import Session                      # noqa: E402
from ledger.timeline import append_tl_locked, read_rows  # noqa: E402
from tools import install as tool_install            # noqa: E402
from warrior import compaction as wc                 # noqa: E402
from warrior import loop as wloop                    # noqa: E402
from warrior.model_client import Reply               # noqa: E402
from warrior.ledger_io import LedgerIO               # noqa: E402
from tests.test_warrior_fake_model import FakeClock  # noqa: E402
from tests.test_warrior_loop import RecSpawn         # noqa: E402
from tests.test_warrior_repair import (              # noqa: E402
    r_done, r_running, write_exec)

W = "warrior:W-1"
IID = "INT-g1-0002"            # fixture 中唯一 pending 意图（kind 空）
TOOL = '{"op":"tool","card":"dig","args":["+short","A","shop.example"]}'
FACT = ('{"op":"ledger","cmd":"add-fact","args":{"intent-id":"INT-g1-0002",'
        '"kind":"info","target":"shop.example",'
        '"detail":"面板返回 200","confidence":"0.7"}}')
DONE = '{"op":"done","reason":"探测完成"}'
DEFAULT_SKILL_MARK = "探隐 TanYin · 总控路由器"   # 根 SKILL.md 首行（默认面锚）


class FakeClient(object):
    """进程内假模型客户端（零端口）：剧本化 Reply + 请求留痕。"""

    def __init__(self, scripts):
        self.channels = [{"name": "m1", "model": "m1"}]
        self.scripts = list(scripts)
        self.requests = []

    def chat(self, messages):
        self.requests.append([dict(m) for m in messages])
        content = (self.scripts.pop(0) if self.scripts
                   else '{"op":"note","text":"剧本尽"}')
        return Reply(True, content=content, model="m1",
                     prompt_tokens=10, completion_tokens=5)


class WiringCase(unittest.TestCase):
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
        self.clock = FakeClock(start=1770000000.0)
        self.spawn = RecSpawn()
        self.addCleanup(shutil.rmtree, self.gd)

    def _loop(self, scripts, **kw):
        args = dict(goal_dir=self.gd, battle_name="B-x",
                    channels=[{"name": "m1", "model": "m1"}], pool=None,
                    warrior_id=W, max_intents=3, max_turns=6, lease_min=30,
                    token_cap=100000, clock=self.clock,
                    tool_spawn=self.spawn, tool_state_path=self.state,
                    ctx_tokens=8000, heartbeat_min=5, stall_min=15)
        args.update(kw)
        lp = wloop.WarriorLoop(**args)
        lp.client = FakeClient(scripts)
        return lp

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    def _exec_rows(self):
        p = os.path.join(self.gd, "tool-executions.tsv")
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            return [ln.split("\t") for ln in f.read().splitlines() if ln]

    def _first_msg(self, lp):
        return lp.client.requests[0][0]["content"]

    def _add_intent(self, kind, detail="接线测试意图"):
        io = LedgerIO(self.gd, W)
        ok, out = io.write("add-intent", {
            "title": "兵种接线意图", "detail": detail, "kind": kind,
            "engine": "web-blackbox", "origin": "llm",
            "budget-share": "100;5;0.5", "priority": "0.9",
            "timestamp": "2026-10-20T10:00:00Z"})
        self.assertEqual(ok, 0, out)
        new = [i for i in io.latest_intents() if i["status"] == "candidate"]
        iid = new[-1]["id"]
        ok, out = io.write("set-intent-status",
                           {"id": iid, "status": "pending",
                            "timestamp": "2026-10-20T10:01:00Z"})
        self.assertEqual(ok, 0, out)
        # 压过 fixture 意图（priority 0.9>0.2）即首选领单
        return iid

    def _park_fixture(self):
        """fixture 意图停入他主长租（不进本次领单/续跑判定面）。"""
        ok, out = LedgerIO(self.gd, "warrior:W-2").claim(
            IID, lease_min=240, ts="2026-10-20T10:00:00Z")
        self.assertTrue(ok, out)

    def _fat_tl(self, n=10, chars=300):
        """写 n 条含意图 id 的肥胖 timeline 行（resume 节素材）。"""
        for i in range(n):
            body = ("warrior-progress warrior=%s intent=%s turn=%d "
                    "op=scan out=脂肪%d%s" % (W, IID, i, i, "x" * chars))
            append_tl_locked(self.gd, "2026-10-20T0%d:30:00Z" % (i % 10),
                             body, actor=W, phase="P3")
        tail = read_rows(self.gd)
        return tail[-1][3], tail[2][3]     # (末行=保留尾, 第3行=被遮蔽头)

    # ================= ① repair 接线 =================

    def test_repair_wires_plan_after_warrior_start(self):
        """正路径：run() 落 warrior-start 后对账悬空执行——合成收尾事件入
        timeline + 状态行原子重写升 orphaned-not-lost，且不阻本世续跑。"""
        lp = self._loop([DONE])
        # 崩溃残留=run() 时刻的盘上态：构造后落盘（构造期池装载会把
        # running 预翻成 orphaned——冻结 executor 既有序，修复面单态源
        # =run() 时盘上文件）
        write_exec(self.gd, [r_running(), r_done()])
        rep = lp.run()
        evs = self._events()
        rep_evs = [e for e in evs if e.startswith("warrior-repair")]
        self.assertEqual(len(rep_evs), 1, "恰一条合成收尾事件")
        self.assertIn("orphaned-not-lost", rep_evs[0])
        self.assertIn("EX-IN-a-t1-c0", rep_evs[0])
        self.assertIn("仅幂等才重试", rep_evs[0])
        i_start = next(i for i, e in enumerate(evs)
                       if e.startswith("warrior-start"))
        self.assertLess(i_start, evs.index(rep_evs[0]),
                        "修复事件落在本世 warrior-start 之后")
        rows = self._exec_rows()
        self.assertEqual(rows[0][2], "orphaned-not-lost",
                         "悬空行状态升级（rc 留空=不假完成）")
        self.assertEqual(rows[0][6], "", "rc 不伪造")
        self.assertEqual(rows[1][2], "completed", "终态行原样")
        self.assertEqual(len(rows[0]), 7, "七列同律")
        self.assertEqual(rep.status, "no-intents", "修复不阻本世续跑")
        self.assertEqual(lp.client.requests and len(lp.client.requests), 1)

    def test_repair_idempotent_across_boots(self):
        """幂等：同盘二次重生不再重开账（事件恰一、状态行不被二改）。"""
        lp1 = self._loop([DONE])
        write_exec(self.gd, [r_running(), r_done()])
        lp1.run()
        lp2 = self._loop([DONE])
        lp2.run()
        self.assertEqual(
            len([e for e in self._events()
                 if e.startswith("warrior-repair")]), 1,
            "已修过的悬空 id 不重开账")
        self.assertEqual(self._exec_rows()[0][2], "orphaned-not-lost",
                         "状态行稳定（不被二改）")

    def test_repair_no_dangling_zero_drift(self):
        """降级：无状态文件/无悬空 → plan None → 零行为漂移（不造文件
        不落事件）。"""
        lp = self._loop([DONE])
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(
            [e for e in self._events() if e.startswith("warrior-repair")],
            [], "无悬空不落修复事件")
        self.assertFalse(os.path.exists(
            os.path.join(self.gd, "tool-executions.tsv")),
            "plan None 不凭空造状态文件")

    # ================= ② compaction 接线 =================

    def test_compaction_replaces_oversized_briefing(self):
        """正路径：ctx 超窗 → 压缩包（summarizer=None 确定性抽取）替换
        首条简报：8 节入面、近尾原文逐字保留、被遮蔽头行整行退场。"""
        fat_last, head_line = self._fat_tl(12)
        skill = os.path.join(self.gd, "..", "small-skill.md")
        with open(skill, "w", encoding="utf-8") as f:
            f.write("# 小协议\n输出 JSON 指令块。")
        lp = self._loop([DONE], ctx_tokens=240, skill_path=skill)
        lp.run()
        first = self._first_msg(lp)
        self.assertIn("<compacted-summary>", first)
        self.assertIn("## Pending Jobs", first,
                      "dsh 固定 8 节结构（防丢任务线索）")
        self.assertIn("## Critical Context", first)
        self.assertNotIn("## 协议", first, "原简报结构不再整块入面")
        self.assertNotIn(head_line, first,
                         "被遮蔽素材整行退场（节内仅 200 字扁平引述）")
        # 近尾原文逐字保留：素材末三行（末条脂肪行+认领+心跳）原样续在
        # 摘要之后（保留预算 38tok 吸收三行——逐字非改写）
        cut = first.index("</compacted-summary>") \
            + len("</compacted-summary>") + 1
        retained = first[cut:]
        self.assertTrue(retained.startswith(fat_last),
                        "保留尾首行=素材末条原文: %r" % retained[:60])
        self.assertIn("set-intent-status %s:active" % IID, retained)
        self.assertIn("warrior-heartbeat", retained)
        # transcript 留痕=实际发出的简报（R4）
        tp = os.path.join(self.gd, "transcripts", IID + ".jsonl")
        with open(tp, encoding="utf-8") as f:
            rec = json.loads(f.readline())
        self.assertEqual(rec["content"], first)

    def test_compaction_protocol_only_sends_full_text(self):
        """降级①：协议面超窗但素材面未超 → build_compaction=None →
        原文照发（零漂移）。"""
        skill = os.path.join(self.gd, "..", "big-skill.md")
        with open(skill, "w", encoding="utf-8") as f:
            f.write("# 大协议\n" + ("规" * 3000))
        lp = self._loop([DONE], ctx_tokens=800, skill_path=skill)
        lp.run()
        first = self._first_msg(lp)
        self.assertIn("## 协议", first)
        self.assertNotIn("<compacted-summary>", first,
                         "素材未超阈值=不产包不压缩")

    def test_compaction_refused_falls_back_full_text(self):
        """降级②：护栏拒（摘要≥被遮蔽）→ 原文照发不炸回合。"""
        self._fat_tl(10)
        skill = os.path.join(self.gd, "..", "small-skill.md")
        with open(skill, "w", encoding="utf-8") as f:
            f.write("# 小协议\n输出 JSON 指令块。")
        with mock.patch.object(
                wloop.compaction, "build_compaction",
                side_effect=wc.CompactionRefused("护栏演习")):
            lp = self._loop([DONE], ctx_tokens=240, skill_path=skill)
            rep = lp.run()
        first = self._first_msg(lp)
        self.assertIn("## 协议", first, "拒=原文照发")
        self.assertNotIn("<compacted-summary>", first)
        self.assertEqual(rep.status, "no-intents", "降级不阻回合收敛")

    # ================= ③ resume_driver 接线 =================

    def _stall_first_life(self, **kw):
        def hook(sp):
            self.clock.advance(60 * 20)     # 超停滞窗 15min
        self.spawn.hook = hook
        lp1 = self._loop([TOOL], **kw)
        self.assertEqual(lp1.run().status, "stalled")
        self.spawn.hook = None
        self.clock.advance(1)
        return lp1

    def test_resume_reborn_life_gets_goal_round_steer(self):
        """正路径：停滞重生入口 build_resume_directive→resume=armed→
        goal_round 防幻觉提示注入 steers（续跑第 1/8 轮+断点意图）。"""
        self._stall_first_life()
        lp2 = self._loop([DONE])
        rep2 = lp2.run()
        self.assertEqual(rep2.status, "no-intents")
        msgs = json.dumps(lp2.client.requests[0], ensure_ascii=False)
        self.assertIn("<goal_round>", msgs)
        self.assertIn(IID, msgs, "断点意图入提示")
        self.assertIn("续跑第 1/8 轮", msgs, "轮计=前世 warrior-start 行数")

    def test_resume_round_limit_stops_rebirth(self):
        """判死：轮计达硬上限 → _stop(round-limit)——不再重生、不落新
        warrior-start、零模型调用。"""
        self._stall_first_life(max_goal_rounds=1, lease_min=120)
        lp2 = self._loop([DONE], max_goal_rounds=1, lease_min=120)
        rep2 = lp2.run()
        self.assertEqual(rep2.status, "round-limit")
        self.assertIn("round-limit 判死", rep2.stop_detail)
        self.assertEqual(lp2.client.requests, [], "判死世零模型调用")
        starts = [e for e in self._events()
                  if e.startswith("warrior-start")]
        self.assertEqual(len(starts), 1, "判死不落新 warrior-start（轮计封顶）")
        self.assertTrue(any("reason=round-limit" in e for e in self._events()),
                        "判死落 warrior-stop 留痕")

    def test_resume_round_limit_idempotent(self):
        """幂等：判死后再重生仍判死（轮计不涨、状态行稳定）。"""
        self._stall_first_life(max_goal_rounds=1, lease_min=120)
        self._loop([DONE], max_goal_rounds=1, lease_min=120).run()
        lp3 = self._loop([DONE], max_goal_rounds=1, lease_min=120)
        rep3 = lp3.run()
        self.assertEqual(rep3.status, "round-limit")
        self.assertEqual(
            len([e for e in self._events() if e.startswith("warrior-start")]),
            1, "反复重生轮计不涨")

    def test_resume_complete_phase_zero_drift(self):
        """降级：盘上无活（complete 相）→ 不注入不判死，走原 no-intents
        停路（零漂移）。"""
        self._park_fixture()
        lp = self._loop([DONE])
        rep = lp.run()
        self.assertEqual(rep.status, "no-intents")
        self.assertEqual(lp.client.requests, [], "无活零模型调用")

    # ================= ④ corps 接线 =================

    def test_corps_skill_card_becomes_briefing_protocol(self):
        """正路径①：领单后 resolve（kind 路由）→ 兵种卡面进简报协议节
        （skill_path 注入位），默认 SKILL.md 不再入面。"""
        self._park_fixture()
        self._add_intent("recon")
        lp = self._loop([DONE])
        lp.run()
        first = self._first_msg(lp)
        self.assertIn("pentest-recon · 侦察兵", first, "侦察兵卡面入简报")
        self.assertIn("只测绘不判定", first)
        self.assertNotIn(DEFAULT_SKILL_MARK, first, "默认面退位")

    def test_corps_ledger_off_face_rejected_rc1(self):
        """正路径②：指令前置 authorize——侦察兵（零写命令）发 add-fact
        → rc1+reason 回模型面，账本零写。"""
        self._park_fixture()
        self._add_intent("recon")
        lp = self._loop([FACT, DONE])
        lp.run()
        self.assertEqual(len(lp.client.requests), 2, "拒后回合继续（结果回模型）")
        msgs = json.dumps(lp2_msgs(lp), ensure_ascii=False)
        self.assertIn("ledger add-fact rc=1", msgs, "拒=rc1")
        self.assertIn("写面越权", msgs, "拒因=兵种写面越权")
        self.assertIn("未执行", msgs)
        facts = Session(self.gd).rows("facts.tsv")
        self.assertFalse(any(len(r) > 4 and r[4] == "面板返回 200"
                             for r in facts), "越权命令零账本写")

    def test_corps_tool_off_face_rejected_no_spawn(self):
        """正路径③：工具面前置——验证官（零工具卡）发 dig → rc1+reason，
        不触工具链（spawn 零调用）。"""
        self._park_fixture()
        self._add_intent("nday-verify")
        lp = self._loop([TOOL, DONE])
        lp.run()
        self.assertEqual(self.spawn.calls, [], "面外工具不执行")
        msgs = json.dumps(lp2_msgs(lp), ensure_ascii=False)
        self.assertIn("tool dig rc=1", msgs)
        self.assertIn("面外命令", msgs, "拒因=面外命令")

    def test_corps_unrouted_intent_degrades_default_face(self):
        """降级①：kind 空+无兵种位 → resolve 无解=降级默认面：默认
        SKILL.md 照旧入简报、authorize 不拦（既有 G-g1 行为零漂移）。"""
        lp = self._loop([FACT, DONE])
        rep = lp.run()
        first = self._first_msg(lp)
        self.assertIn(DEFAULT_SKILL_MARK, first, "降级=默认面照旧")
        facts = Session(self.gd).rows("facts.tsv")
        self.assertTrue(any(len(r) > 4 and r[4] == "面板返回 200"
                            for r in facts), "无兵种上下文不执法（零漂移）")
        self.assertEqual(rep.status, "no-intents")

    def test_corps_bad_yaml_degrades_default_face(self):
        """降级②：corps.yaml 形错（fail-loud 面）→ 装配降级 corps_rt=None
        → kind 路由意图也走默认面。"""
        with open(os.path.join(self.gd, "corps.yaml"), "w",
                  encoding="utf-8") as f:
            f.write("bogus_key: 1\n")
        self._park_fixture()
        self._add_intent("recon")
        lp = self._loop([DONE])
        lp.run()
        first = self._first_msg(lp)
        self.assertIn(DEFAULT_SKILL_MARK, first, "坏配置=降级默认面不炸")


def lp2_msgs(lp):
    """第二轮请求的 messages（含指令结果回执）。"""
    return lp.client.requests[1]


if __name__ == "__main__":
    unittest.main()
