# -*- coding: utf-8 -*-
"""批次 1 T7-T11 查询/校验/special 测试——python3 -m unittest tests.test_query_check

范范式：临时目录拷贝 tests/fixtures/G-g1 起底（不动夹具本体）；虚构数据只用 .example 域。
每条查询命令 ≥1 正例；校验类每条含构造 FAIL 例（改夹具副本触发）。
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)
from ledger import core

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(CLI, "tanyin-ledger")
REDACT = os.path.join(CLI, "tanyin-redact")
GUARD = os.path.join(CLI, "tanyin-guard")
T = core.TABLES


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.g = os.path.join(self.td.name, "G-g1")
        shutil.copytree(FIX, self.g)

    def cli(self, cmd, *args):
        return subprocess.run([sys.executable, LEDGER, cmd, "--goal-dir", self.g] + list(args),
                              capture_output=True, text=True)

    def rows(self, t):
        return core.read_tsv(os.path.join(self.g, t), len(T[t]))

    def write(self, t, rows):
        core.write_tsv(os.path.join(self.g, t), rows)

    def append_tl(self, event, revert="", ts="2026-09-23T12:00:00Z",
                  actor="CLI", phase="P6.0"):
        rows = self.rows("timeline.tsv")
        prev = rows[-1][T["timeline.tsv"].index("hash")] if rows else core.GENESIS
        wo = [ts, actor, phase, event, revert, prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, revert, prev, h, "2"])
        self.write("timeline.tsv", rows)

    def add_edge(self, eid, kind, src, dst):
        rows = self.rows("edges.tsv")
        rows.append(row("edges.tsv", id=eid, kind=kind, source_id=src, target_id=dst,
                        provenance="test", schema_version="2"))
        self.write("edges.tsv", rows)


# ---------------------------------------------------------------- T7 查询命令

class QueryCommands(Base):
    def test_unconsumed_facts(self):
        r = self.cli("unconsumed-facts")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#count=2")
        self.assertEqual(lines[1].split(chr(9))[0], "F-g1-0001")
        self.assertEqual(len(lines[1].split(chr(9))), 4)  # id/kind/target/confidence
        # top-N 摘要化：计数不变、行流截断（先于消费验证，2 条仅列 1 条）
        r = self.cli("unconsumed-facts", "--top=1")
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#count=2")
        self.assertEqual(len(lines), 2)
        # 消费后剔除：derived_from 出边（fact→intent）
        self.add_edge("E-g1-0003", "derived_from", "F-g1-0001", "INT-g1-0002")
        r = self.cli("unconsumed-facts")
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#count=1")
        self.assertEqual(lines[1].split(chr(9))[0], "F-g1-0002")

    def test_pending_intents(self):
        r = self.cli("pending-intents")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#count=1")
        f = lines[1].split(chr(9))
        self.assertEqual(f[0], "INT-g1-0002")
        self.assertEqual(len(f), 5)  # id/title/kind/engine/budget_share
        # 事件溯源取最新：追加 active 行后不再 pending
        rows = self.rows("intents.tsv")
        rows.append(row("intents.tsv", id="INT-g1-0002", title="admin 面板未授权访问",
                        status="active", engine="web-blackbox", kind="authz-diff",
                        budget_share="0.2", schema_version="2"))
        self.write("intents.tsv", rows)
        r = self.cli("pending-intents")
        self.assertEqual(r.stdout.splitlines()[0], "#count=0")

    def test_pending_intents_empty_ledger(self):
        d = os.path.join(self.td.name, "G-empty")
        os.makedirs(d)
        r = subprocess.run([sys.executable, LEDGER, "pending-intents", "--goal-dir", d],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "#count=0")

    def test_matrix_gaps_default(self):
        r = self.cli("matrix-gaps")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#count=1")
        self.assertEqual(lines[1], "web.api" + chr(9) + "inj.sql")

    def test_matrix_gaps_baseline(self):
        r = self.cli("matrix-gaps", "--baseline")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        line = r.stdout.splitlines()[0]
        self.assertIn("#baseline_rows=3", line)
        self.assertIn("#in_scope_surfaces=2", line)
        # 夹具 attack_surface 命名与 assets.value 不一致 → covered=false
        self.assertIn("covered=false", line)
        # 构造覆盖：攻击面=资产值
        self.write("matrix.tsv", [
            row("matrix.tsv", attack_surface="shop.example", vuln_class="authn.missing",
                state="?", intent_id="INT-g1-0002", schema_version="2"),
            row("matrix.tsv", attack_surface="shop.example", vuln_class="authz.diff",
                state="x", reason="FD-g1-0001", intent_id="INT-g1-0002", schema_version="2"),
            row("matrix.tsv", attack_surface="admin-internal.shop.example", vuln_class="inj.sql",
                state="", schema_version="2"),
        ])
        r = self.cli("matrix-gaps", "--baseline")
        self.assertIn("covered=true", r.stdout.splitlines()[0])

    def test_converge_check(self):
        r = self.cli("converge-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "running")  # 空格未清零+fact 未消费
        # converged：空格清零 + facts 全消费 + 无 blocked + 预算未穿
        self.write("matrix.tsv", self.rows("matrix.tsv") + [
            row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="x",
                reason="补测完成", intent_id="INT-g1-0001", schema_version="2")])
        self.add_edge("E-g1-0003", "derived_from", "F-g1-0001", "INT-g1-0002")
        self.add_edge("E-g1-0004", "derived_from", "F-g1-0002", "INT-g1-0002")
        r = self.cli("converge-check")
        self.assertEqual(r.stdout.splitlines()[0], "converged")
        # budget-exhausted：goal 根 token 穿
        rows = self.rows("budget.tsv")
        rows.append(row("budget.tsv", token_delta="9000000", requests_delta="0",
                        hours_delta="0", dollars_delta="0", scope="goal", note="爆量",
                        schema_version="2"))
        self.write("budget.tsv", rows)
        r = self.cli("converge-check")
        self.assertEqual(r.stdout.splitlines()[0], "budget-exhausted")

    def test_intent_status(self):
        r = self.cli("intent-status", "--id=INT-g1-0002")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0].split(chr(9)),
                         ["INT-g1-0002", "pending", ""])
        r = self.cli("intent-status", "--id=INT-g1-9999")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "#count=0")
        r = self.cli("intent-status")
        self.assertEqual(r.returncode, 2)  # 用法错误

    def test_matrix_get(self):
        r = self.cli("matrix-get", "--attack-surface=web.admin-panel", "--vuln-class=authz.diff")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0].split(chr(9)),
                         ["web.admin-panel", "authz.diff", "x", "FD-g1-0001",
                          "INT-g1-0002", ""])
        r = self.cli("matrix-get", "--attack-surface=nope", "--vuln-class=inj.sql")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "#count=0")
        # 事件溯源同键取最新
        self.write("matrix.tsv", self.rows("matrix.tsv") + [
            row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authz.diff",
                state="?", reason="复测存疑", intent_id="INT-g1-0002", schema_version="2")])
        r = self.cli("matrix-get", "--attack-surface=web.admin-panel", "--vuln-class=authz.diff")
        self.assertEqual(r.stdout.splitlines()[0].split(chr(9))[2], "?")

    def test_scope_check_all_assets(self):
        r = self.cli("scope-check", "--all-assets")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "#judged=3/3")
        rows = self.rows("assets.tsv")
        rows[2][T["assets.tsv"].index("in_scope")] = ""  # 制造未判定
        self.write("assets.tsv", rows)
        r = self.cli("scope-check", "--all-assets")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0], "#judged=2/3")
        self.assertEqual(r.stdout.splitlines()[1].split(chr(9))[0], "AST-g1-0003")

    def test_scope_check_single_value(self):
        for val, expect in [("admin-internal.shop.example", "in_scope"),
                            ("10.10.5.5", "in_scope"),
                            ("evil.example", "out_of_scope"),
                            ("192.168.0.1", "out_of_scope")]:
            t = "subdomain" if val[0].isalpha() else "ip"
            r = self.cli("scope-check", "--type=" + t, "--value=" + val)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(r.stdout.splitlines()[0], expect, val)
        r = self.cli("scope-check")
        self.assertEqual(r.returncode, 2)  # 用法错误：二选一模式必选

    def test_budget_check(self):
        r = self.cli("budget-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads(r.stdout.splitlines()[0])
        self.assertEqual(data["goal"]["budget"], "2M;50000;40")
        self.assertEqual(data["goal"]["used"]["token"], 20000)   # 12000+8000 上卷
        self.assertEqual(data["goal"]["used"]["requests"], 65)
        self.assertEqual(data["goal"]["left"]["token"], 1980000)
        self.assertEqual([i["id"] for i in data["intents"]],
                         ["INT-g1-0001", "INT-g1-0002"])       # 排序确定
        i2 = data["intents"][1]
        self.assertEqual(i2["share"]["token"], 400000)          # 0.2×2M
        self.assertEqual(i2["used"]["token"], 8000)
        self.assertEqual(i2["left"]["token"], 392000)

    def test_cleanup_checklist_default(self):
        r = self.cli("cleanup-checklist")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], "#items=1")
        self.assertEqual(lines[1].split(chr(9)),
                         ["2026-09-23T01:00:00Z", "add-goal G-g1-0001", "irreversible",
                          "pending"])

    def test_cleanup_verify_fail_then_reverted(self):
        r = self.cli("cleanup-checklist", "--verify")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))
        self.assertIn("未核销行=1", r.stdout)
        # 落 revert 事件 → all_reverted
        self.append_tl("revert:add-goal G-g1-0001")
        r = self.cli("cleanup-checklist", "--verify")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "all_reverted")

    def test_cleanup_verify_exempted(self):
        rows = self.rows("approvals.tsv")
        rows.append(row("approvals.tsv", id="AP-g1-0002", command_hash="e" * 64,
                        decision="exempted", approver="user",
                        timestamp="2026-09-23T12:00:00Z", note="add-goal G-g1-0001",
                        schema_version="2"))
        self.write("approvals.tsv", rows)
        r = self.cli("cleanup-checklist", "--verify")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "exemptions_complete")


# ---------------------------------------------------------------- T8 校验命令

class CheckCommands(Base):
    def test_hash_recheck_pass_and_chain_fail(self):
        r = self.cli("hash-recheck")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("PASS"))
        rows = self.rows("timeline.tsv")
        rows[1][T["timeline.tsv"].index("event")] += "X"   # 篡改历史行
        self.write("timeline.tsv", rows)
        r = self.cli("hash-recheck")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))

    def test_hash_recheck_ev_dual_track(self):
        from ledger import check_cmds
        art_dir = os.path.join(self.g, "artifacts")
        os.makedirs(art_dir)
        art = os.path.join(art_dir, "ev1.txt")
        open(art, "w", encoding="utf-8").write("line1\n2026-09-23T01:00:00Z nonce=abc123\nline3\n")
        raw, norm = check_cmds.artifact_hashes(art)
        rows = self.rows("E-index.tsv")
        rows[0][T["E-index.tsv"].index("artifact_path")] = "artifacts/ev1.txt"
        rows[0][T["E-index.tsv"].index("content_hash_raw")] = raw
        rows[0][T["E-index.tsv"].index("content_hash_norm")] = norm
        self.write("E-index.tsv", rows)
        r = self.cli("hash-recheck")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # 双轨比对通过
        open(art, "a", encoding="utf-8").write("tampered\n")   # 工件被改 → 失配
        r = self.cli("hash-recheck")
        self.assertEqual(r.returncode, 1)
        self.assertIn("EV-g1-0001", r.stdout)

    def test_matrix_audit(self):
        r = self.cli("matrix-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "PASS" + chr(9) + "sampled=0" + chr(9) + "warnings=0")
        # '-' 格带理由 → 抽查通过
        self.write("matrix.tsv", [
            row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="-",
                reason="组件不存在", intent_id="INT-g1-0001", schema_version="2")])
        r = self.cli("matrix-audit")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sampled=1", r.stdout.splitlines()[0])
        # FAIL 例 1：'-' 格无理由（reason 强制）
        self.write("matrix.tsv", [
            row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="-",
                schema_version="2")])
        r = self.cli("matrix-audit")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))
        # FAIL 例 2：批量置态与 fact 密度不符告警（6 格仅 2 fact）
        rows = [row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="x",
                    reason="置态", intent_id="INT-g1-0001", schema_version="2")]
        for i in range(6):
            rows.append(row("matrix.tsv", attack_surface="web.api", vuln_class="wstg-%02d" % i,
                            state="x", reason="置态", intent_id="INT-g1-0001",
                            schema_version="2"))
        self.write("matrix.tsv", rows)
        r = self.cli("matrix-audit")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("INT-g1-0001", r.stdout)

    def test_state_rebuild(self):
        r = self.cli("state-rebuild")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "PASS" + chr(9) + "revision=4")
        open(os.path.join(self.g, "state.md"), "w", encoding="utf-8").write("revision: 4\n")
        r = self.cli("state-rebuild")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        open(os.path.join(self.g, "state.md"), "w", encoding="utf-8").write("revision: 3\n")
        r = self.cli("state-rebuild")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))

    def test_scope_coverage(self):
        r = self.cli("ledger-scope-coverage")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # 夹具缺 exclude/oob
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))
        self.assertIn("exclude", r.stdout)
        self.assertIn("oob", r.stdout)
        rows = self.rows("scope.tsv")
        rows.append(row("scope.tsv", id="S-g1-0003", kind="exclude", matcher="10.11.0.0/16",
                        note="界外段", schema_version="2"))
        rows.append(row("scope.tsv", id="S-g1-0004", kind="oob", matcher="c2.example:8443",
                        note="OOB 回连", schema_version="2"))
        self.write("scope.tsv", rows)
        r = self.cli("ledger-scope-coverage")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("PASS"))

    def test_tree_check(self):
        r = self.cli("ledger-tree-check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # 两个子域缺 parent
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))
        self.add_edge("E-g1-0003", "parent", "AST-g1-0002", "AST-g1-0001")
        self.add_edge("E-g1-0004", "parent", "AST-g1-0003", "AST-g1-0001")
        r = self.cli("ledger-tree-check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("PASS"))
        # 环：root 挂到子域下
        self.add_edge("E-g1-0005", "parent", "AST-g1-0001", "AST-g1-0003")
        r = self.cli("ledger-tree-check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_replay_summary(self):
        r = self.cli("ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # C3 无重放义务
        self.assertTrue(r.stdout.splitlines()[0].startswith("PASS"))
        rows = self.rows("findings.tsv")
        rows[0][T["findings.tsv"].index("confidence")] = "C1"
        self.write("findings.tsv", rows)
        r = self.cli("ledger-replay-summary")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # C1 未重放
        self.assertIn("FD-g1-0001", r.stdout)
        self.cli("set-replay-state", "--id=FD-g1-0001", "--state=VERIFIED")
        r = self.cli("ledger-replay-summary")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("verified=1", r.stdout.splitlines()[0])

    def test_terminal_gate(self):
        r = self.cli("ledger-terminal-gate")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # 空格未清零
        self.assertTrue(r.stdout.splitlines()[0].startswith("FAIL"))
        self.assertIn("web.api", r.stdout)
        self.write("matrix.tsv", self.rows("matrix.tsv") + [
            row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="x",
                reason="补测完成", intent_id="INT-g1-0001", schema_version="2")])
        r = self.cli("ledger-terminal-gate")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 锚点未冻结 → FAIL
        rows = [list(r_) for r_ in self.rows("matrix.tsv")]
        for r_ in rows:
            r_[T["matrix.tsv"].index("frozen_at")] = ""
        self.write("matrix.tsv", rows)
        r = self.cli("ledger-terminal-gate")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


# ------------------------------------------------------- T11 set-replay-state

class SetReplayState(Base):
    def test_verified_writes_and_chain_alive(self):
        r = self.cli("set-replay-state", "--id=FD-g1-0001", "--state=VERIFIED")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "OK" + chr(9) + "replay:FD-g1-0001:VERIFIED")
        frows = self.rows("findings.tsv")
        self.assertEqual(len(frows), 2)  # 追加联动行（纯追加）
        latest = frows[-1]
        self.assertEqual(latest[T["findings.tsv"].index("exploitation_status")], "verified")
        self.assertEqual(latest[T["findings.tsv"].index("confidence")], "C3")  # 维持不降
        trows = self.rows("timeline.tsv")
        self.assertEqual(trows[-1][T["timeline.tsv"].index("event")],
                         "replay:FD-g1-0001:VERIFIED")
        r = self.cli("verify-chain")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # 链延续有效

    def test_rejected_downgrades(self):
        rows = self.rows("findings.tsv")
        rows[0][T["findings.tsv"].index("confidence")] = "C1"
        self.write("findings.tsv", rows)
        r = self.cli("set-replay-state", "--id=FD-g1-0001", "--state=REJECTED")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        latest = self.rows("findings.tsv")[-1]
        self.assertEqual(latest[T["findings.tsv"].index("confidence")], "C3")  # 降 C3
        self.assertEqual(latest[T["findings.tsv"].index("exploitation_status")], "suspected")

    def test_ev_replay_via_linked_finding(self):
        r = self.cli("set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.rows("findings.tsv")), 1)  # 无 linked_finding 不联动
        rows = self.rows("E-index.tsv")
        rows[0][T["E-index.tsv"].index("linked_finding")] = "FD-g1-0001"
        self.write("E-index.tsv", rows)
        r = self.cli("set-replay-state", "--id=EV-g1-0001", "--state=VERIFIED")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.rows("findings.tsv")), 2)

    def test_rejects(self):
        r = self.cli("set-replay-state", "--id=FD-g1-0001", "--state=NOPE")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        r = self.cli("set-replay-state", "--id=FD-g1-9999", "--state=VERIFIED")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        for _ in range(2):
            r = self.cli("set-replay-state", "--id=FD-g1-0001", "--state=REPAIRED")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("set-replay-state", "--id=FD-g1-0001", "--state=REPAIRED")
        self.assertEqual(r.returncode, 1)  # 重试计数>max_retry=2
        self.assertIn("REJECT", r.stderr)


# ------------------------------------------------------------- T9 redact-scan

class RedactScan(Base):
    def test_pass_on_fixture(self):
        r = self.cli("redact-scan")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "PASS" + chr(9) + "leaks=0")

    def test_detect_leaks_with_location(self):
        frows = self.rows("facts.tsv")
        frows[0][T["facts.tsv"].index("detail")] = "password=Hunter2secret"
        frows[1][T["facts.tsv"].index("detail")] = "密钥 {{vault:cred-9}} 泄漏"
        self.write("facts.tsv", frows)
        erows = self.rows("E-index.tsv")
        erows[0][T["E-index.tsv"].index("raw_excerpt")] = "AKIAIOSFODNN7EXAMPLE"
        self.write("E-index.tsv", erows)
        crows = self.rows("creds.tsv")
        crows[0][T["creds.tsv"].index("secret_ref")] = "plaintext-hunter2"  # 真值形态
        self.write("creds.tsv", crows)
        r = self.cli("redact-scan")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "FAIL" + chr(9) + "leaks=4")
        for loc in ["facts.tsv:1:detail", "facts.tsv:2:detail",
                    "E-index.tsv:1:raw_excerpt", "creds.tsv:1:secret_ref"]:
            self.assertIn(loc, r.stdout)

    def test_placeholder_whitelist_repro_command(self):
        erows = self.rows("E-index.tsv")
        erows[0][T["E-index.tsv"].index("repro_command")] = \
            "curl -H 'Authorization: {{vault:cred-1}}' https://shop.example/"
        self.write("E-index.tsv", erows)
        r = self.cli("redact-scan")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # 契约 01 §3.9 白名单列

    def test_tanyin_redact_entry(self):
        r = subprocess.run([sys.executable, REDACT, "--goal-dir", FIX],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0], "PASS" + chr(9) + "leaks=0")
        # 报告文本模式：占位符零泄漏（P5 交付前终检）
        rep = os.path.join(self.td.name, "report")
        os.makedirs(rep)
        open(os.path.join(rep, "final.md"), "w", encoding="utf-8").write(
            "凭据 {{vault:cred-1}} 未替换\n")
        r = subprocess.run([sys.executable, REDACT, "--goal-dir", FIX,
                            "--target=" + rep], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("final.md", r.stdout)
        r = subprocess.run([sys.executable, REDACT], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


# ------------------------------------------------------------- T10 tanyin-guard

class GuardSkeleton(unittest.TestCase):
    def test_skeleton(self):
        for args in ([], ["anything"]):
            r = subprocess.run([sys.executable, GUARD] + args,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("guard 骨架", r.stdout)
            self.assertIn("批次 2", r.stdout)


if __name__ == "__main__":
    unittest.main()
