# -*- coding: utf-8 -*-
"""功能13补件二·定时复验器 ③三态回写钩子（retest-settle）测试。

判定映射（复验纪律单源=tanyin-replay 三态判定，别重造）：
  reproduced→仍真（VERIFIED 既有门+last_verified 刷新）
  env-diff→已修复（REPAIRED 既有语义→report_artifacts lifecycle repair-candidate 桶，不另造桶）
  not-reproduced→环境变更（关旧开新沿既有 supersedes 机制，须 --new-finding 指向
  已铸 supersedes 链的新行）；blocked 偏置=任一 EV 最新 not-reproduced 即 env-changed
  （与 set-replay-state G-52 门同款 fail-closed 偏置）。
python3 -m unittest tests.test_retest_settle
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)
from ledger import core

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(CLI, "tanyin-ledger")
T = core.TABLES
NOW = "2026-10-20T09:00:00Z"
FD = "FD-g1-0101"
EV = "EV-g1-0002"


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
        self.seed_finding()

    def cli(self, cmd, *args):
        return subprocess.run([sys.executable, LEDGER, cmd, "--goal-dir", self.g] + list(args),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def rows(self, t):
        return core.read_tsv(os.path.join(self.g, t), len(T[t]))

    def write(self, t, rows):
        core.write_tsv(os.path.join(self.g, t), rows)

    def seed_finding(self):
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id=FD, intent_id="INT-g1-0002",
                        title="待复验发现", confidence="C1", impact="高",
                        exploitation_status="verified", dedup_key="AST-g1-0002+CVE-2026-0001",
                        vuln_ref="CVE-2026-0001", scope_check="in_scope",
                        description_brief="b", reproducible_steps="s1;s2",
                        affected_asset_id="AST-g1-0002", evidence_ids=EV,
                        status="active", created="2026-10-01T09:00:00Z"))
        self.write("findings.tsv", rows)
        ev = self.rows("E-index.tsv")
        ev.append(row("E-index.tsv", id=EV, title="EV", source_type="command",
                      observed_at="2026-10-01T08:00:00Z", network_position="internet",
                      repro_command="curl http://x.example/", repro_kind="single",
                      artifact_path="a/" + EV, linked_finding=FD,
                      created="2026-10-01T08:00:00Z"))
        self.write("E-index.tsv", ev)

    def append_tl(self, event, ts="2026-10-20T08:00:00Z"):
        rows = self.rows("timeline.tsv")
        prev = rows[-1][T["timeline.tsv"].index("hash")] if rows else core.GENESIS
        wo = [ts, "CLI", "P4", event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, "CLI", "P4", event, "", prev, h, "2"])
        self.write("timeline.tsv", rows)

    def events(self):
        return [r[T["timeline.tsv"].index("event")] for r in self.rows("timeline.tsv")]

    def latest_finding(self, fid=FD):
        out = None
        for r in self.rows("findings.tsv"):
            if r[0] == fid:
                out = r
        return out

    def seed_supersede(self, new_fd="FD-g1-0201"):
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id=new_fd, intent_id="INT-g1-0002",
                        title="环境变更后重开发现", confidence="C1", impact="高",
                        exploitation_status="verified", dedup_key="AST-g1-0002+CVE-2026-0001",
                        vuln_ref="CVE-2026-0001", scope_check="in_scope",
                        description_brief="b2", reproducible_steps="s1;s3",
                        affected_asset_id="AST-g1-0002", evidence_ids=EV,
                        status="active", created=NOW))
        old = list(self.latest_finding())
        old[T["findings.tsv"].index("status")] = "superseded"
        old[T["findings.tsv"].index("created")] = NOW
        rows.append(old)
        self.write("findings.tsv", rows)
        er = self.rows("edges.tsv")
        er.append(row("edges.tsv", id="E-g1-0099", kind="supersedes", source_id=FD,
                      target_id=new_fd, provenance="supersede-finding", created=NOW))
        self.write("edges.tsv", er)

    def seed_retest_card(self, status="active"):
        rows = self.rows("intents.tsv")
        rows.append(row("intents.tsv", id="INT-g1-0101", title="retest " + FD + " #1",
                        detail="[retest:%s] 原EV=%s 重放命令=tanyin-replay replay --id=%s" % (FD, EV, EV),
                        status=status, engine="replay", kind="nday-verify", origin="entity",
                        dedup_key="AST-g1-0002+nday-verify+retest " + FD + " #1",
                        budget_share="1;1;1", created="2026-10-20T08:30:00Z"))
        self.write("intents.tsv", rows)

    def latest_intent(self, iid):
        out = None
        for r in self.rows("intents.tsv"):
            if r[0] == iid:
                out = r
        return out


class StillTrue(Base):
    def test_evidence_ids_only_discovery(self):
        # evidence-first 流水：EV 先落账（linked_finding 空），finding 行自书引用——
        # 判定/门/report 三方同源吃 evidence_ids（补件二对齐修）
        rows = self.rows("E-index.tsv")
        rows[-1][T["E-index.tsv"].index("linked_finding")] = ""
        self.write("E-index.tsv", rows)
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.latest_finding()[T["findings.tsv"].index("created")], NOW)

    def test_reproduced_refreshes_last_verified(self):
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        f = self.latest_finding()
        self.assertEqual(f[T["findings.tsv"].index("exploitation_status")], "verified")
        self.assertEqual(f[T["findings.tsv"].index("created")], NOW)   # last_verified 刷新（既有形）
        evs = self.events()
        self.assertTrue(any(e.startswith("replay:%s:VERIFIED" % FD) for e in evs))
        self.assertTrue(any(e == "retest:%s:still-true last_verified=%s" % (FD, NOW)
                            for e in evs))

    def test_closes_active_retest_card_done(self):
        self.seed_retest_card(status="active")
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        c = self.latest_intent("INT-g1-0101")
        self.assertEqual(c[T["intents.tsv"].index("status")], "done")
        self.assertIn("retest-settled", c[T["intents.tsv"].index("reason")])

    def test_closes_candidate_retest_card_rejected(self):
        self.seed_retest_card(status="candidate")
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        c = self.latest_intent("INT-g1-0101")
        self.assertEqual(c[T["intents.tsv"].index("status")], "rejected")


class Fixed(Base):
    def test_env_diff_lands_repaired_repair_candidate(self):
        self.append_tl("replay-probe %s verdict=env-diff" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        evs = self.events()
        # 对齐 report_artifacts lifecycle：末值 REPAIRED→tri=env-diff→repair-candidate 桶
        self.assertTrue(any(e.startswith("replay:%s:REPAIRED" % FD) for e in evs))
        self.assertTrue(any(e == "retest:%s:fixed repair-candidate" % FD for e in evs))
        f = self.latest_finding()
        self.assertEqual(f[T["findings.tsv"].index("created")], NOW)


class EnvChanged(Base):
    def test_not_reproduced_requires_new_finding(self):
        self.append_tl("replay-probe %s verdict=not-reproduced" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("supersede", r.stderr)

    def test_not_reproduced_with_chain_settles(self):
        self.append_tl("replay-probe %s verdict=not-reproduced" % EV)
        self.seed_supersede()
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW,
                     "--new-finding=FD-g1-0201")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any(e.startswith("retest:%s:env-changed superseded-by=FD-g1-0201" % FD)
                            for e in self.events()))
        self.assertEqual(self.latest_finding()[T["findings.tsv"].index("status")], "superseded")

    def test_new_finding_without_chain_rejects(self):
        self.append_tl("replay-probe %s verdict=not-reproduced" % EV)
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id="FD-g1-0201", intent_id="INT-g1-0002",
                        title="无链新行", confidence="C1", impact="低",
                        exploitation_status="verified", dedup_key="AST-g1-0002+CVE-2026-0001",
                        scope_check="in_scope", description_brief="b",
                        reproducible_steps="s1", affected_asset_id="AST-g1-0002",
                        evidence_ids=EV, status="active", created=NOW))
        self.write("findings.tsv", rows)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW,
                     "--new-finding=FD-g1-0201")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("supersedes", r.stderr)

    def test_blocked_bias_mixed_probes_go_env_changed(self):
        # EV-2 最新 reproduced、EV-3 最新 not-reproduced：blocked 偏置（G-52 同款）
        ev = self.rows("E-index.tsv")
        ev.append(row("E-index.tsv", id="EV-g1-0003", title="EV3", source_type="command",
                      observed_at="2026-10-01T08:00:00Z", network_position="internet",
                      repro_command="curl http://y.example/", repro_kind="single",
                      artifact_path="a/EV-g1-0003", linked_finding=FD,
                      created="2026-10-01T08:00:00Z"))
        self.write("E-index.tsv", ev)
        self.append_tl("replay-probe EV-g1-0003 verdict=reproduced")
        self.append_tl("replay-probe %s verdict=not-reproduced" % EV)
        self.seed_supersede()
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW,
                     "--new-finding=FD-g1-0201")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any(e.startswith("retest:%s:env-changed" % FD) for e in self.events()))


class Discipline(Base):
    def test_no_probe_rejects(self):
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("实证", r.stderr)

    def test_manual_verdict_rejects(self):
        self.append_tl("replay-probe %s verdict=manual" % EV)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_settle_twice_idempotent_reject(self):
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        self.assertEqual(self.cli("retest-settle", "--id=" + FD,
                                  "--timestamp=" + NOW).returncode, 0)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("已回写", r.stderr)

    def test_unknown_fd_rejects(self):
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        r = self.cli("retest-settle", "--id=FD-nope", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_superseded_fd_rejects(self):
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        rows = self.rows("findings.tsv")
        old = list(self.latest_finding())
        old[T["findings.tsv"].index("status")] = "superseded"
        rows.append(old)
        self.write("findings.tsv", rows)
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_timestamp_required(self):
        r = self.cli("retest-settle", "--id=" + FD)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_new_probe_after_settle_allows_resettle(self):
        self.append_tl("replay-probe %s verdict=reproduced" % EV)
        self.assertEqual(self.cli("retest-settle", "--id=" + FD,
                                  "--timestamp=" + NOW).returncode, 0)
        self.append_tl("replay-probe %s verdict=env-diff" % EV, ts="2026-10-21T08:00:00Z")
        r = self.cli("retest-settle", "--id=" + FD, "--timestamp=2026-10-21T09:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any(e.startswith("replay:%s:REPAIRED" % FD) for e in self.events()))


if __name__ == "__main__":
    unittest.main()
