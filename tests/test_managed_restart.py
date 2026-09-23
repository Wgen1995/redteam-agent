# -*- coding: utf-8 -*-
"""批次 3 T6：受管重启护栏四件套（速率上限/计入预算/单活跃会话/timeline 事件）。"""
import io, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core, phases_engine as pe, state_md, write_cmds

FIX = os.path.join(HERE, "fixtures", "G-g1")
T0 = "2026-09-24T10:00:00Z"
T1 = "2026-09-24T10:05:00Z"   # 距 T0 5 分钟 < 10 分钟默认窗
T2 = "2026-09-24T10:20:00Z"   # 距 T0 20 分钟 > 窗


def snap_all(gd):
    out = {}
    for t in core.TABLES:
        p = os.path.join(gd, t)
        out[t] = open(p, "rb").read() if os.path.exists(p) else None
    for extra in ("state.md",):
        p = os.path.join(gd, extra)
        out[extra] = open(p, "rb").read() if os.path.exists(p) else None
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def restart(self, *args):
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.dispatch("restart", self.gd, list(args))
        return code, buf_o.getvalue(), buf_e.getvalue()

    def events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]

    def budget_last(self):
        return core.read_tsv(os.path.join(self.gd, "budget.tsv"), 8)[-1]

    def snap(self):
        return snap_all(self.gd)


class TestRestart(Base):
    def test_happy_path_writes_guardrails(self):
        code, out, err = self.restart("--spawn=auto", "--timestamp=" + T0)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any(e.startswith("managed-restart spawn=auto") for e in self.events()))
        bl = self.budget_last()
        self.assertEqual(bl[5], "goal")
        self.assertIn("managed-restart spawn=auto", bl[6])
        self.assertEqual(bl[1], "2000")   # token_delta=RESTART_TOKEN_COST 计入预算
        f, _, errs = state_md.parse_state(os.path.join(self.gd, "state.md"))
        self.assertEqual(errs, [])
        self.assertEqual(f["spawn"], "auto")
        self.assertEqual(f["session_status"], "active")
        # ⑥ T7 接通：重启收尾重生成 resume-kit（恢复注入白名单）
        self.assertIn("恢复注入白名单",
                      open(os.path.join(self.gd, "resume-kit.md"), encoding="utf-8").read())

    def test_rate_limit_second_restart_within_window(self):
        self.restart("--spawn=auto", "--timestamp=" + T0)
        before = self.snap()
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T1)
        self.assertEqual(code, 1)
        self.assertIn("restart-rate-limit", out)
        self.assertEqual(self.snap(), before)   # 零副作用

    def test_rate_window_elapsed_ok(self):
        self.restart("--spawn=auto", "--timestamp=" + T0)
        code, out, err = self.restart("--spawn=auto", "--timestamp=" + T2)
        self.assertEqual(code, 0, out + err)

    def test_auto_cannot_takeover_active_lock(self):
        write_cmds.HANDLERS["checkpoint"](self.gd,
            ["--session=s-owner", "--phase=P3", "--timestamp=" + T0])
        before = self.snap()
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T1)
        self.assertEqual(code, 1)
        self.assertIn("单活跃会话", out)
        self.assertEqual(self.snap(), before)

    def test_manual_takeover_with_rebuild_ok(self):
        write_cmds.HANDLERS["checkpoint"](self.gd,
            ["--session=s-owner", "--phase=P3", "--timestamp=" + T0])
        code, out, err = self.restart("--spawn=manual", "--timestamp=" + T2)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(any("takeover-of=s-owner" in e for e in self.events()))

    def test_broken_chain_refuses(self):
        p = os.path.join(self.gd, "timeline.tsv")
        rows = core.read_tsv(p, 8)
        rows[2][3] = "tampered"
        core.write_tsv(p, rows)
        code, out, _ = self.restart("--spawn=auto", "--timestamp=" + T0)
        self.assertEqual(code, 1)
        self.assertIn("链", out)

    def test_budget_reflects_restart_cost(self):
        from ledger import query_cmds
        before = query_cmds.budget_tree(core.Session(self.gd))["goal"]["used"]["token"]
        self.restart("--spawn=auto", "--timestamp=" + T0, "--token-cost=500")
        after = query_cmds.budget_tree(core.Session(self.gd))["goal"]["used"]["token"]
        self.assertEqual(after - before, 500)

    # ---- 自加钉死例（计划未列；T3/T5 同型先例，HANDOFF 记账）----

    def test_usage_errors_exit_2(self):
        # 退出码纪律：用法/参数非法=2（非裸异常）
        for args in (["--spawn=never", "--timestamp=" + T0],
                     ["--spawn=auto"],
                     ["--spawn=auto", "--timestamp=" + T0, "--rate-minutes=abc"],
                     ["--spawn=auto", "--timestamp=" + T0, "--token-cost=1.5"],
                     ["--spawn=auto", "--timestamp=" + T0, "--bogus=1"]):
            code, out, err = self.restart(*args)
            self.assertEqual(code, 2, "args=%r out=%r err=%r" % (args, out, err))

    def test_event_actor_is_master(self):
        # 接口冻结：managed-restart 事件 actor=总控（经 append-timeline 逐字落账）
        self.restart("--spawn=auto", "--timestamp=" + T0)
        rows = core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)
        hit = [r for r in rows if r[3].startswith("managed-restart spawn=auto")]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0][1], "总控")

    def test_restart_leaves_reconciled_state(self):
        # 重启收尾不变式：state.md 与账本对账一致（revision≡timeline 行数+snapshot 重算相等）
        self.restart("--spawn=auto", "--timestamp=" + T0)
        f, _, errs = state_md.parse_state(os.path.join(self.gd, "state.md"))
        self.assertEqual(errs, [])
        rows = core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)
        self.assertEqual(int(f["revision"]), len(rows))
        self.assertEqual(f["snapshot"], state_md.snapshot_from_session(core.Session(self.gd)))


if __name__ == "__main__":
    unittest.main()
