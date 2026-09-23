# -*- coding: utf-8 -*-
"""批次 3 T4/T5：state.md v2（结构冻结/200 行硬顶/原子写/单活跃会话锁）+ state-rebuild 对账。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, state_md, write_cmds

FIX = os.path.join(HERE, "fixtures", "G-g1")
TAB = chr(9)
TS = "2026-09-24T09:00:00Z"


def snap_all(gd):
    out = {}
    for t in core.TABLES:
        p = os.path.join(gd, t)
        out[t] = open(p, "rb").read() if os.path.exists(p) else None
    for extra in ("state.md", "resume-kit.md"):
        p = os.path.join(gd, extra)
        out[extra] = open(p, "rb").read() if os.path.exists(p) else None
    return out


def tl_events(gd):
    ev = core.TABLES["timeline.tsv"].index("event")
    return [r[ev] for r in core.read_tsv(os.path.join(gd, "timeline.tsv"), 8)]


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def ck(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = write_cmds.HANDLERS["checkpoint"](self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()

    def state_path(self):
        return os.path.join(self.gd, "state.md")

    def read_state(self):
        return state_md.parse_state(self.state_path())

    def events(self):
        return tl_events(self.gd)

    def snap(self):
        return snap_all(self.gd)

    def n_tl(self):
        return len(core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8))


class TestCheckpointV2(Base):
    def test_writes_frozen_structure(self):
        base = self.n_tl()
        code, out, _ = self.ck("--session=s-1", "--phase=P3", "--round=4",
                               "--note=line1\nline2", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        fields, handoff, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(list(fields), state_md.KEY_ORDER)
        self.assertEqual(fields["revision"], str(base + 1))   # Ruling①：revision=落账后 timeline 行数
        self.assertEqual(fields["session"], "s-1")
        self.assertEqual(fields["session_status"], "active")
        self.assertEqual(fields["spawn"], "fresh")
        self.assertEqual(fields["phase"], "P3")
        self.assertEqual(fields["round"], "4")
        self.assertEqual(fields["updated"], TS)
        self.assertEqual(fields["resume_kit"], "resume-kit.md")
        self.assertEqual(handoff, ["line1", "line2"])
        self.assertTrue(fields["snapshot"].startswith("intents_pending=1;"))  # 夹具 INT-g1-0002=pending

    def test_revision_equals_timeline_rows(self):
        # Ruling① 钉死：state-rebuild 对账基准=timeline 行数（T5 消费；撕裂态=timeline 领先）
        self.ck("--session=s-1", "--timestamp=" + TS)
        fields, _, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(int(fields["revision"]), self.n_tl())

    def test_revision_monotonic_and_timeline_event(self):
        base = self.n_tl()
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, out, _ = self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        self.assertIn("revision=%d" % (base + 2), out)
        self.assertTrue(any(e.startswith("checkpoint revision=%d" % (base + 2)) for e in self.events()))

    def test_single_active_session_lock(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        before = self.snap()
        code, _, err = self.ck("--session=s-2", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("单活跃会话", err)
        self.assertEqual(self.snap(), before)   # 零变更（timeline 也不动——预检前置）

    def test_release_then_takeover(self):
        base = self.n_tl()
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, _, _ = self.ck("--session=s-1", "--release", "--timestamp=" + TS)
        self.assertEqual(code, 0)
        fields, _, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(fields["session_status"], "released")
        self.assertEqual(fields["revision"], str(base + 2))
        self.assertTrue(any("release" in e for e in self.events()))
        code, out, _ = self.ck("--session=s-2", "--timestamp=" + TS)   # 已释放可接管
        self.assertEqual(code, 0)
        self.assertIn("revision=%d" % (base + 3), out)

    def test_same_session_recheckpoint_ok(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        code, _, _ = self.ck("--session=s-1", "--round=2", "--timestamp=" + TS)
        self.assertEqual(code, 0)   # 同 session 每轮可重打（否则首锁卡死全部轮次）

    def test_200_line_hard_cap(self):
        note = "\n".join("h%d" % i for i in range(300))
        before = self.snap()
        code, _, err = self.ck("--session=s-1", "--note=" + note, "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("200", err)
        self.assertFalse(os.path.exists(self.state_path()))
        self.assertEqual(self.snap(), before)   # 预检前置=timeline 也零变更

    def test_atomic_write_no_tmp_leftover(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertFalse(os.path.exists(self.state_path() + ".tmp"))
        self.assertTrue(os.path.isfile(self.state_path()))

    def test_tier0_no_goal_reject(self):
        os.remove(os.path.join(self.gd, "goals.tsv"))
        code, _, err = self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("Tier0", err)

    def test_corrupt_state_rejects(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        with open(self.state_path(), "w", encoding="utf-8", newline="\n") as f:
            f.write("garbage line no colon\n")
        before = self.snap()   # 注入撕裂后拍基线：拒收不得再动任何字节
        code, _, err = self.ck("--session=s-1", "--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("rebuild-state", err)
        self.assertEqual(self.snap(), before)   # 零落账


class TestRebuild(Base):
    """批次 3 T5：state-rebuild v2 对账（snapshot 漂移检测）+ rebuild-state 对账重建。

    撕裂三态（kill -9 保真度语义，设计 §4.1/§5）：
      A=state.md.tmp 残留（原子写中断）→ rebuild-state 清扫；
      B=timeline 领先 state（checkpoint 落账后、写盘前被杀）→ state-rebuild FAIL → 重建；
      C=state.md 缺失（首跑/被清）→ rebuild-state 以账本为准初始化。
    链断（人为篡改 timeline）≠撕裂：不可自愈，拒绝重建（halt 人工处置）。"""

    def _rebuild_check(self):
        from ledger import check_cmds
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = check_cmds.HANDLERS["state-rebuild"](self.gd, [])
        return code, buf.getvalue()

    def _rebuild_state(self, *args):
        from ledger import phases_engine as pe
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pe.dispatch("rebuild-state", self.gd, list(args))
        return code, buf.getvalue()

    def test_state_rebuild_pass_after_checkpoint(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        code, out = self._rebuild_check()
        self.assertEqual(code, 0)
        self.assertIn("PASS\trevision=", out)

    def test_state_rebuild_detects_snapshot_drift(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        # 撕裂态 B 等价构造：checkpoint 后账本又前进一行（timeline 领先 state）
        write_cmds.HANDLERS["append-timeline"](self.gd, [
            "--actor=CLI", "--phase=P3", "--event=drift", "--timestamp=" + TS])
        code, out = self._rebuild_check()
        self.assertEqual(code, 1)
        self.assertIn("rebuild-state", out)

    def test_state_rebuild_detects_snapshot_tamper(self):
        # T5 对账实质：revision 一致而 snapshot 与账本重算不一致（v2 新增检查项）
        self.ck("--session=s-1", "--timestamp=" + TS)
        fields, handoff, errs = self.read_state()
        self.assertEqual(errs, [])
        fields["snapshot"] = ("intents_pending=99;facts_unconsumed=99;"
                              "matrix_gaps=99;budget_token_left=99")
        state_md.write_state(self.state_path(), fields, handoff)
        code, out = self._rebuild_check()
        self.assertEqual(code, 1)
        self.assertIn("snapshot 漂移", out)
        self.assertIn("rebuild-state", out)

    def test_rebuild_state_repairs(self):
        self.ck("--session=s-1", "--phase=P3", "--timestamp=" + TS)
        os.remove(self.state_path())   # 撕裂态 C：state.md 缺失
        code, out = self._rebuild_state("--timestamp=" + TS)
        self.assertEqual(code, 0, out)
        fields, _, errs = self.read_state()
        self.assertEqual(errs, [])
        self.assertEqual(fields["session_status"], "released")   # 重建=锁释放（防双活）
        self.assertEqual(fields["session"], "rebuilt")
        self.assertEqual(fields["spawn"], "manual")
        code, out = self._rebuild_check()   # 重建后再对账=PASS
        self.assertEqual(code, 0)

    def test_rebuild_state_clears_tmp_leftover(self):
        self.ck("--session=s-1", "--timestamp=" + TS)
        with open(self.state_path() + ".tmp", "w", encoding="utf-8", newline="\n") as f:
            f.write("torn")   # 撕裂态 A：tmp 残留
        code, out = self._rebuild_state("--timestamp=" + TS)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.state_path() + ".tmp"))

    def test_rebuild_state_refuses_broken_chain(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"   # 破坏中间事件→断链
        core.write_tsv(p, rows)
        code, out = self._rebuild_state("--timestamp=" + TS)
        self.assertEqual(code, 1)
        self.assertIn("链", out)


if __name__ == "__main__":
    unittest.main()
