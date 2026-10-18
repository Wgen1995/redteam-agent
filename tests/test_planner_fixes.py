# -*- coding: utf-8 -*-
"""评审打回复盘：规划者 I-1/I-2/I-3/I-4+M-5 修复（TDD 红测试先行）。

评审源：docs/reviews/2026-10-20-review-sentinel-planner.md §二——
  I-1 REJECT 走 stderr（_run 只捕 stdout→拒绝原因全空、dedup 竞速合并
     分支死代码、竞速真发生=RuntimeError 杀常驻循环，run() 无兜底）
  I-2 TANYIN_APPROVAL_KEY 在场时 _redispatch 机械审批必崩（须 --sig 签名）
  I-3 事件驱动闭环未接线（收卡惰性触发 + CLI start/trigger 两入口）
  I-4 sweep O(I×N)（万格同构基准 8s+→头部一趟聚合+Session 全 sweep 复用）
  M-5 _reach_set 图构建重复两次（自建 _build 后 reachable_gap_cells 又建）

跑法：python3 -m unittest tests.test_planner_fixes -v
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import time
import unittest

try:
    from unittest import mock
except ImportError:                                    # pragma: no cover
    mock = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)

from ledger import registry                            # noqa: E402
from ledger import planner_loop as PL                  # noqa: E402
from ledger import replacer as RP                      # noqa: E402
from ledger.core import Session, TABLES                # noqa: E402
from ledger import timeline as TL                      # noqa: E402
from tests.test_planner_loop import _mkgoal, FakeClock  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-10-20T10:00:00Z"
_IT = TABLES["intents.tsv"].index("title")
_ID = TABLES["intents.tsv"].index("detail")
_IS = TABLES["intents.tsv"].index("status")
_EV = TABLES["timeline.tsv"].index("event")

BAD_KIND_ARGS = ["--title=x", "--detail=d", "--engine=web-blackbox",
                 "--kind=bogus", "--origin=adjacency", "--budget-share=1;1;1",
                 "--timestamp=" + TS]


def run(gd, cmd, *args):
    """CLI 级既有入口（同 test_planner_replacer.run 单源口径）。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    if rc != 0:
        raise AssertionError("%s rc=%d: %s" % (cmd, rc, buf.getvalue()))
    return buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = _mkgoal(self._tmp.name)

    def rows(self, t):
        return Session(self.gd).rows(t)


# ============================================================ I-1 stderr 捕获 ==

class TestRunCapturesRejection(Base):
    """I-1：write_cmds._wrap 把 REJECT 写 stderr——_run 只捕 stdout 则
    坏参数时 out=''（拒绝原因全空）。修法=stdout+stderr 合并捕获。"""

    def test_planner_run_carries_reject_reason(self):
        rc, out = PL._run(self.gd, "add-intent", list(BAD_KIND_ARGS))
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out)
        self.assertIn("kind 不在枚举", out, "拒绝原因须随合并文本带回（排障面）")

    def test_replacer_run_carries_reject_reason(self):
        rc, out = RP._run(self.gd, "add-intent", list(BAD_KIND_ARGS))
        self.assertEqual(rc, 1)
        self.assertIn("REJECT", out)
        self.assertIn("kind 不在枚举", out)


# ======================================================== I-1 dedup 竞速合并 ==

class TestDedupRaceMerged(Base):
    """I-1：竞速合并分支曾是死代码（"dedup_key" 判在空 out 上）——模拟
    并发战士在 existing 快照之后、add-intent 落账之前先铸同 dedup 卡：
    真命中=合并不 raise（RuntimeError 会杀死常驻循环/炸 sweep）。"""

    def _race_lookup(self, race_args):
        """首见 add-intent 时先经真通道铸 race_args 卡（=并发方先落账）。"""
        real_lookup = registry.lookup
        state = {"raced": False}

        def fake(cmd):
            h = real_lookup(cmd)
            if cmd == "add-intent" and not state["raced"]:
                state["raced"] = True
                rc = h(self.gd, list(race_args))
                self.assertEqual(rc, 0, "竞速方先铸须成功")
            return h
        return fake

    def test_assess_race_merges_instead_of_raising(self):
        race_title = PL.intent_title("admin.shop.example", "inj.sql")
        race_args = ["--title=" + race_title, "--detail=竞速方先落",
                     "--engine=web-blackbox", "--kind=matrix-test",
                     "--origin=adjacency", "--budget-share=1;1;1",
                     "--priority=0.9000", "--timestamp=" + TS]
        with mock.patch.object(registry, "lookup",
                               self._race_lookup(race_args)):
            added = PL.assess(self.gd, TS)            # 不得 raise（I-1）
        titles = sorted(r[_IT] for r in self.rows("intents.tsv")
                        if r[_IT].startswith("planner: "))
        both = sorted([PL.intent_title("admin.shop.example", "inj.sql"),
                       PL.intent_title("admin.shop.example", "wstg-inpv")])
        self.assertEqual(titles, both,
                         "竞速卡并入（回放特例律），另一空格本轮照常派")
        self.assertEqual(len(added), 1)
        raced = [r for r in self.rows("intents.tsv")
                 if r[_IT] == race_title][-1]
        self.assertIn("竞速方先落", raced[_ID], "在账的=竞速方铸的卡（真合并）")

    def test_continue_card_race_merges_instead_of_raising(self):
        run(self.gd, "add-intent", "--title=半程卡", "--detail=剩余: 补测",
            "--engine=web-blackbox", "--kind=matrix-test",
            "--origin=recon-event", "--budget-share=1;1;1",
            "--priority=0.5", "--timestamp=" + TS)
        iid = [r[0] for r in self.rows("intents.tsv")
               if r[_IT] == "半程卡"][-1]
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=active",
            "--timestamp=" + TS)
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=blocked",
            "--reason=预算中断", "--timestamp=" + TS)
        race_args = ["--title=续接: 半程卡", "--detail=竞速方先落",
                     "--engine=web-blackbox", "--kind=matrix-test",
                     "--origin=recon-event", "--budget-share=1;1;1",
                     "--priority=0.5", "--timestamp=" + TS]
        with mock.patch.object(registry, "lookup",
                               self._race_lookup(race_args)):
            out = RP.sweep(self.gd, TS)               # 不得 raise（I-1）
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["continue-closeout"])
        cont = [r for r in self.rows("intents.tsv")
                if r[_IT] == "续接: 半程卡"]
        self.assertEqual(len(cont), 1, "竞速续接卡并入，恰一张（幂等）")
        self.assertIn("竞速方先落", cont[-1][_ID])


# ======================================================== I-1 run() 兜底 ==

class TestRunSurvivesRoundCrash(Base):
    """I-1：run() 无兜底——单轮异常直接杀死常驻循环。修法=异常记事件
    入账本（append-timeline 既有通道，可回放）后继续轮询。"""

    def test_run_records_event_and_survives(self):
        clock = FakeClock()
        loop = PL.PlannerLoop(self.gd, ts_fn=lambda: TS,
                              mono=clock.mono, sleep=clock.sleep,
                              poll_interval=0.1)
        orig = loop._round
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("round-1 崩（探针）")
            return orig()

        loop._round = flaky
        TL.append_tl_locked(self.gd, TS, "战士写回: 新线索", "warrior:W-1", "P3")
        n = loop.run(max_rounds=2)
        self.assertEqual(n, 2, "常驻循环不死于单轮异常")
        self.assertEqual(len(calls), 2)
        evs = [r[_EV] for r in self.rows("timeline.tsv")]
        self.assertTrue(any(e.startswith("planner-round-fail") for e in evs),
                        "单轮异常须记事件入账本: %r" % evs[-5:])
        self.assertTrue(any("round-1" in e for e in evs),
                        "事件须带异常原因（排障面）")


# ============================================================ I-2 持钥重派 ==

class TestKeyedFaultRedispatch(Base):
    """I-2：TANYIN_APPROVAL_KEY 在场（生产姿态，HANDOFF B2）时 approve
    强制 --sig=HMAC-SHA256(sha256(key), command_hash)——重派臂恰在加固
    部署里崩。修法=机械审批走同一持钥签名通道（密钥来源=环境，同律；
    HMAC 式复用 write_cmds 单源，不自铸第二份）。"""

    def _fault_card(self):
        run(self.gd, "add-intent", "--title=断线卡", "--detail=剩余: 逐项",
            "--engine=web-blackbox", "--kind=recon", "--origin=recon-event",
            "--budget-share=1;1;1", "--timestamp=" + TS)
        iid = [r[0] for r in self.rows("intents.tsv")
               if r[_IT] == "断线卡"][-1]
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=active",
            "--timestamp=" + TS)
        run(self.gd, "set-intent-status", "--id=" + iid, "--status=blocked",
            "--reason=transport-fault: egress 断连", "--timestamp=" + TS)
        return iid

    def test_sweep_fault_redispatch_under_approval_key(self):
        import hashlib
        from ledger.write_cmds import Ctx, _row_sig_ok
        iid = self._fault_card()
        key = "unit-approval-key"
        with mock.patch.dict(os.environ, {"TANYIN_APPROVAL_KEY": key}):
            out = RP.sweep(self.gd, TS)             # 不得 raise（I-2）
        self.assertEqual([v["verdict"] for v in out if v["intent_id"] == iid],
                         ["fault-redispatch"])
        self.assertEqual([r for r in self.rows("intents.tsv")
                          if r[0] == iid][-1][_IS], "active",
                         "持钥部署下纯故障重派照常重入池")
        chash = hashlib.sha256(
            ("set-intent-status --id=%s --status=active" % iid)
            .encode("utf-8")).hexdigest()
        aps = [r for r in self.rows("approvals.tsv")
               if r[TABLES["approvals.tsv"].index("command_hash")] == chash]
        self.assertEqual(len(aps), 1, "机械审批恰一行（全审计）")
        self.assertTrue(_row_sig_ok(Ctx(self.gd), aps[0], key.encode("utf-8")),
                        "审批行 sig 须可被持钥方复算验证"
                        "（HMAC-SHA256(sha256(key), command_hash)）")
        # 幂等：active 非终态，二扫不再铸审批
        with mock.patch.dict(os.environ, {"TANYIN_APPROVAL_KEY": key}):
            RP.sweep(self.gd, TS)
        aps2 = [r for r in self.rows("approvals.tsv")
                if r[TABLES["approvals.tsv"].index("command_hash")] == chash]
        self.assertEqual(len(aps2), 1)


# ============================================================ I-4 线性扫面 ==

_ITC = TABLES["intents.tsv"]
_TLC = TABLES["timeline.tsv"]
_FAC = TABLES["facts.tsv"]
_MAC = TABLES["matrix.tsv"]


def _bench_goal(tmp, n_int=1000, tl_per=30, fa_per=20):
    """同构万格基准夹具（评审 I-4 口径：时间线 30k+facts 20k=评审 10k
    基准的表规模；意图数 1/10=1k，全部 done 终态——sweep 纯扫面零写入，
    量的是扫面本身）。"""
    from ledger.core import write_tsv
    gd = shutil.copytree(FIX, os.path.join(tmp, "G-bench"))
    its, tls, fas, mts = [], [], [], []
    ii, it = _ITC.index("id"), _ITC.index("title")
    ist, ien, icr = (_ITC.index("status"), _ITC.index("engine"),
                     _ITC.index("created"))
    tev = _TLC.index("event")
    tts = _TLC.index("timestamp")
    fid, fint = _FAC.index("id"), _FAC.index("intent_id")
    fkind, fcr = _FAC.index("kind"), _FAC.index("created")
    mas, mvc, mint = (_MAC.index("attack_surface"), _MAC.index("vuln_class"),
                      _MAC.index("intent_id"))
    for i in range(1, n_int + 1):
        iid = "INT-g1-%04d" % i
        row = [""] * len(_ITC)
        row[ii], row[it], row[ist] = iid, "意图 %04d" % i, "done"
        row[ien], row[icr] = "web-blackbox", TS
        its.append(row)
        for k in range(tl_per):
            t = [""] * len(_TLC)
            t[tts] = TS
            t[tev] = "add-intent %s turn=%d" % (iid, k)
            tls.append(t)
        for k in range(fa_per):
            f = [""] * len(_FAC)
            f[fid], f[fint], f[fkind], f[fcr] =                 "F-%04d-%03d" % (i, k), iid, "info", TS
            fas.append(f)
        m = [""] * len(_MAC)
        m[mas], m[mvc], m[mint] = "web.x%04d" % i, "inj.sql", iid
        mts.append(m)
    write_tsv(os.path.join(gd, "intents.tsv"), its)
    write_tsv(os.path.join(gd, "timeline.tsv"), tls)
    write_tsv(os.path.join(gd, "facts.tsv"), fas)
    write_tsv(os.path.join(gd, "matrix.tsv"), mts)
    write_tsv(os.path.join(gd, "findings.tsv"), [])   # 夹具残留 finding 不掺产出计数
    return gd


class TestSweepLinear(unittest.TestCase):
    """I-4：sweep O(I×N)（每意图三全表扫+逐动作重开 Session 全量重读盘）
    ——评审实测万格 8.32s/轮。修法=头部一趟聚合+Session 全 sweep 复用。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_ten_k_scale_tables_sweep_under_1s(self):
        gd = _bench_goal(self._tmp.name)     # tl 30k + facts 20k + 1k 意图
        t0 = time.monotonic()
        out = RP.sweep(gd, TS)
        dt = time.monotonic() - t0
        self.assertEqual(len(out), 1000)
        self.assertEqual({v["verdict"] for v in out}, {"complete"})
        self.assertEqual(sum(v["trace_lines"] for v in out),
                         1000 * 30, "trace 聚合口径=每意图 30 行生命周期")
        self.assertEqual(sum(v["outputs"] for v in out), 1000 * 20)
        self.assertLess(dt, 1.0,
                        "sweep 须一趟聚合线性：同构万格基准表规模（时间线"
                        "30k+facts20k）在 1k 意图上 <1s（评审 I-4 实测旧路径 "
                        "8.32s@10k，本机复刻 2.7s）")

    def test_sweep_reuses_single_session(self):
        gd = shutil.copytree(FIX, os.path.join(self._tmp.name, "G-t"))
        n = 20
        for i in range(n):
            run(gd, "add-intent", "--title=死路卡%02d" % i,
                "--detail=探过了", "--engine=web-blackbox", "--kind=recon",
                "--origin=entity", "--budget-share=1;1;1",
                "--timestamp=" + TS)
            iid = [r[0] for r in Session(gd).rows("intents.tsv")
                   if r[_IT] == "死路卡%02d" % i][-1]
            run(gd, "set-intent-status", "--id=" + iid,
                "--status=rejected", "--reason=此路不通", "--timestamp=" + TS)
        n_facts_before = len(Session(gd).rows("facts.tsv"))
        real_session = RP.core.Session
        made = []

        def counting(d):
            made.append(d)
            return real_session(d)

        with mock.patch.object(RP.core, "Session", new=counting):
            out = RP.sweep(gd, TS)
        self.assertEqual(len([v for v in out
                              if v["verdict"] == "boundary-solidify"]), n)
        self.assertEqual(len(out), n + 1)   # +1=夹具 INT-g1-0001 done=complete
        facts = Session(gd).rows("facts.tsv")
        self.assertEqual(len(facts), n_facts_before + n, "每卡恰一条收口事实")
        self.assertEqual(len(made), 1 + n,
                         "Session 全 sweep 复用一只（1=sweep 头 + %d=每卡"
                         "一笔 add-fact 写路径 Ctx 各自的 Session；评审 I-4："
                         "逐意图重开 Session=全量重读盘）" % n)


if __name__ == "__main__":
    unittest.main()
