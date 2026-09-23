# -*- coding: utf-8 -*-
"""批次 3 T11：干跑 eval——P0-P2 零对外请求（设计 §11 批次 3 出口①；PROTOCOL.md §3 口径）。
dry_run_p0_p2 驱动=总控行为的确定性脚本化：每条命令都与 SKILL.md/九门 md 序列一一对应，
亦是 T12 kill -9 eval 的底座。"""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core

LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
PHASES_CLI = os.path.join(ROOT, "cli", "tanyin-phases")
EGRESS = os.path.join(ROOT, "cli", "tanyin-egress")
A64 = "a" * 64
TS = "2026-09-24T12:00:00Z"

# --- 追加件（完备性设计 2bd6052 已批衍生）：总控行为纪律检查的测试侧仪表 ---
# 调用窗日志：budget-check 等只读命令零账本痕迹，调用事实由本表承载（不改产物/引擎）。
CALLS = []

# 表→命令事件词映射（write_cmds/matrix_init 各 ctx.event 落点全集）：纪律②的解释词汇。
# timeline.tsv 不列=自证（自身完整性由 verify-chain 链式哈希承载，见主 eval 断言）。
TABLE_EVENTS = {
    "goals.tsv": ("add-goal",),
    "scope.tsv": ("add-scope", "amend-scope"),
    "intents.tsv": ("add-intent", "set-intent-status"),
    "facts.tsv": ("add-fact",),
    "findings.tsv": ("add-finding", "supersede-finding"),
    "assets.tsv": ("add-asset",),
    "edges.tsv": ("add-edge", "supersede-finding"),
    "approvals.tsv": ("approve",),
    "E-index.tsv": ("add-evidence",),
    "matrix.tsv": ("matrix-init", "matrix-set", "matrix-freeze"),
    "budget.tsv": ("budget-log",),
    "creds.tsv": ("add-cred", "set-cred-status"),
}


def ledger(gd, cmd, args=()):
    r = subprocess.run([sys.executable, LEDGER, cmd, "--goal-dir", gd] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    CALLS.append(("ledger", cmd, r.returncode))
    return r.returncode, r.stdout, r.stderr


def phases(gd, sub, args=()):
    r = subprocess.run([sys.executable, PHASES_CLI, sub, "--goal-dir", gd] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    CALLS.append(("phases", sub, r.returncode))
    return r.returncode, r.stdout, r.stderr


def _egress_compile(gd):
    r = subprocess.run([sys.executable, EGRESS, "compile", "--goal-dir", gd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


STEPS = [
    # --- P0：八问落账（干跑：授权书用本地自建文件占位）---
    ("P0", lambda gd: ledger(gd, "add-goal", [
        "--target=dryrun.example", "--objective=干跑自检",
        "--auth-doc=auth/dry.pdf", "--auth-sha256=" + A64, "--signer=self",
        "--valid-from=2026-09-01", "--valid-until=2026-09-30",
        "--budget=2M;50000;40", "--model-tier=strong", "--guard-tier=T3",
        "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "budget-check")),   # 预算门在位（追加件③：立项即读预算）
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=include",
        "--matcher=*.dryrun.example", "--note=干跑", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=exclude",
        "--matcher=db.dryrun.example", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "add-scope", ["--kind=oob",
        "--matcher=cb.dryrun.example", "--timestamp=" + TS])),
    ("P0", lambda gd: ledger(gd, "append-timeline", ["--actor=总控", "--phase=P0",
        "--event=skill-version sha=dryrun tools.lock=dryrun", "--timestamp=" + TS])),
    ("P0", _egress_compile),                      # 干跑：只 compile（本地产物）
    ("P0", lambda gd: phases(gd, "gate", ["--phase=P0", "--timestamp=" + TS])),
    # --- P1：测绘（干跑：本地虚构资产，不派侦察子代理、零请求）---
    ("P1", lambda gd: ledger(gd, "add-asset", ["--type=root-domain",
        "--value=dryrun.example", "--meta=dry", "--timestamp=" + TS])),
    ("P1", lambda gd: phases(gd, "gate", ["--phase=P1", "--timestamp=" + TS])),
    # --- P2：规划（matrix-freeze 由 gate P2 断言①真跑）---
    ("P2", lambda gd: ledger(gd, "matrix-init", ["--timestamp=" + TS])),
    ("P2", lambda gd: phases(gd, "gate", ["--phase=P2", "--timestamp=" + TS])),
]


def dry_run_p0_p2(gd, upto=None):
    """顺序执行 STEPS；返回 (最后退出码, 已执行步数)。任何步退出 2=序列自身缺陷，即停。"""
    code, done = 0, 0
    for i, (gate, fn) in enumerate(STEPS):
        if upto is not None and i >= upto:
            break
        r = fn(gd)
        code = r[0] if isinstance(r, tuple) else r
        done = i + 1
        if code == 2:
            return 2, done
    return code, done


def fresh_drydir(td, name="G-dryrun"):
    gd = os.path.join(td, name)
    os.makedirs(os.path.join(gd, "auth"), exist_ok=True)
    with open(os.path.join(gd, "auth", "dry.pdf"), "w", encoding="utf-8") as f:
        f.write("dry")
    return gd


class BaseDryRun(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = fresh_drydir(self.td.name)

    def events(self):
        ev = core.TABLES["timeline.tsv"].index("event")
        return [r[ev] for r in core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)]


class TestDryRun(BaseDryRun):
    def test_p0_p2_all_gates_zero_egress_requests(self):
        code, done = dry_run_p0_p2(self.gd)
        self.assertEqual(code, 0, "干跑序列第 %d 步退出码 %r" % (done, code))
        evs = self.events()
        self.assertFalse([e for e in evs if e.startswith("request:")],
                         "出现对外请求事件（PROTOCOL.md §3 违规）")
        self.assertFalse([e for e in evs if "request-ticket" in e])
        for g in ("P0", "P1", "P2"):
            self.assertTrue(any(e.startswith("gate-exit:" + g) and "result=PASS" in e
                                for e in evs), "缺 " + g + " 过门事件")
        code, out, _ = ledger(self.gd, "verify-chain")
        self.assertEqual(code, 0, out)
        code, out, _ = ledger(self.gd, "state-rebuild")
        self.assertEqual(code, 0, out)   # state.md absent=合法 PASS

    def test_deterministic_two_runs_same_event_count(self):
        gd2 = fresh_drydir(self.td.name, "G-dryrun2")
        dry_run_p0_p2(self.gd)
        dry_run_p0_p2(gd2)
        n1 = len(core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8))
        n2 = len(core.read_tsv(os.path.join(gd2, "timeline.tsv"), 8))
        self.assertEqual(n1, n2)   # 同 ts 驱动=同事件数（T12 确定性依赖）


class TestDiscipline(BaseDryRun):
    """追加件：总控行为纪律三断言（最小可行口径，Ruling 记 HANDOFF）。
    ① 九门顺序未跳：gate-exit 首现序恰为 P0→P1→P2（无缺漏、无越位、无门外门）。
    ② 无绕账本直写：eval 前后 13 表内容 diff，每张变化表在窗口内新增的 timeline
       事件里必有 ≥1 条命令事件词可解释（简化口径；timeline 自证=verify-chain）。
    ③ 预算门在位：budget-check 在 eval 窗口内被调用过且全部退出 0。"""

    def _snap(self):
        out = {}
        for t in core.TABLES:
            p = os.path.join(self.gd, t)
            out[t] = open(p, "rb").read() if os.path.exists(p) else b""
        return out

    def test_gate_exit_order_no_skip(self):
        dry_run_p0_p2(self.gd)
        seq = []
        for e in self.events():
            m = core.GATE_EXIT_EVENT.match(e)
            if m and m.group(1) not in seq:
                seq.append(m.group(1))
        self.assertEqual(seq, ["P0", "P1", "P2"],
                         "gate-exit 首现序!=P0→P1→P2（跳门/越位）: %r" % seq)

    def test_table_diff_explained_by_timeline(self):
        before = self._snap()
        n_before = len(self.events()) if os.path.exists(
            os.path.join(self.gd, "timeline.tsv")) else 0
        dry_run_p0_p2(self.gd)
        new_events = self.events()[n_before:]
        after = self._snap()
        changed = [t for t in core.TABLES if after[t] != before[t]]
        for t in changed:
            if t == "timeline.tsv":
                continue   # 自证：链一致性由 verify-chain 断言承载
            pats = TABLE_EVENTS[t]
            ok = [e for e in new_events if e.startswith(pats)]
            self.assertTrue(ok, "表 %s 内容变化无 timeline 命令事件可解释"
                            "（绕账本直写嫌疑）；窗口新增事件=%r" % (t, new_events))

    def test_budget_gate_invoked(self):
        mark = len(CALLS)
        dry_run_p0_p2(self.gd)
        hits = [c for c in CALLS[mark:] if c[1] == "budget-check"]
        self.assertTrue(hits, "预算门缺位：eval 窗口内未调用 budget-check")
        self.assertEqual([c[2] for c in hits], [0] * len(hits),
                         "budget-check 非零退出: %r" % hits)


if __name__ == "__main__":
    unittest.main()
