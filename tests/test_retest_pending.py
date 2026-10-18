# -*- coding: utf-8 -*-
"""功能13补件二·定时复验器 ①过期清单（retest-pending）测试。

范式同 tests/test_query_check：临时目录拷贝 tests/fixtures/G-g1 起底；
last_verified ≡ findings 事件溯源最新行 created（沿用 set-replay-state/
set-cred-status 刷新既有形——13 表列集冻结不新增物理列，探知注记13 同律）。
python3 -m unittest tests.test_retest_pending
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)
from ledger import core

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(CLI, "tanyin-ledger")
T = core.TABLES
NOW = "2026-10-20T09:00:00Z"


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
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def rows(self, t):
        return core.read_tsv(os.path.join(self.g, t), len(T[t]))

    def write(self, t, rows):
        core.write_tsv(os.path.join(self.g, t), rows)

    def add_finding(self, fid, created, exploitation="verified", asset="AST-g1-0002",
                    evidence="EV-g1-0002", status="active"):
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id=fid, intent_id="INT-g1-0002",
                        title="复验靶 " + fid, confidence="C1", impact="高",
                        exploitation_status=exploitation, dedup_key="dk-" + fid,
                        scope_check="in_scope", description_brief="b",
                        reproducible_steps="s1;s2", affected_asset_id=asset,
                        evidence_ids=evidence, status=status, created=created))
        self.write("findings.tsv", rows)

    def add_ev(self, evid, fd):
        rows = self.rows("E-index.tsv")
        rows.append(row("E-index.tsv", id=evid, title="EV " + evid, source_type="command",
                        observed_at="2026-09-23T01:00:00Z", network_position="internet",
                        repro_command="curl http://x.example/", repro_kind="single",
                        artifact_path="a/" + evid, linked_finding=fd,
                        created="2026-09-23T01:00:00Z"))
        self.write("E-index.tsv", rows)


class PendingList(Base):
    def test_overdue_verified_listed(self):
        self.add_finding("FD-g1-0101", "2026-10-01T09:00:00Z")   # 19 天前
        self.add_ev("EV-g1-0002", "FD-g1-0101")
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0].split(chr(9))[0], "#pending=1")
        f = lines[1].split(chr(9))
        self.assertEqual(f[0], "FD-g1-0101")
        self.assertEqual(f[3], "2026-10-01T09:00:00Z")   # last_verified=最新行 created
        self.assertEqual(f[4], "19")                     # age_days
        self.assertEqual(f[5], "EV-g1-0002")

    def test_recent_not_listed_default_7d(self):
        self.add_finding("FD-g1-0101", "2026-10-19T09:00:00Z")   # 1 天前
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.splitlines()[0].split(chr(9))[0], "#pending=0")
        # 边界：恰满 7 天=过期（窗口到期即须复验）；6 天不过窗
        self.add_finding("FD-g1-0102", "2026-10-13T09:00:00Z")   # 恰 7 天
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertIn("FD-g1-0102", r.stdout)
        self.add_finding("FD-g1-0103", "2026-10-14T09:00:01Z")   # 6.99 天
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertNotIn("FD-g1-0103", r.stdout)

    def test_goal_config_window(self):
        with open(os.path.join(self.g, "retest.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"window_days": 3}, f)
        self.add_finding("FD-g1-0101", "2026-10-17T09:00:00Z")   # 3 天：按 3 天窗=过期
        self.add_finding("FD-g1-0102", "2026-10-18T09:00:00Z")   # 2 天：未过窗
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("FD-g1-0101", r.stdout)
        self.assertNotIn("FD-g1-0102", r.stdout)
        self.assertIn("window_days=3", r.stdout.splitlines()[0])

    def test_window_flag_overrides_config(self):
        self.add_finding("FD-g1-0101", "2026-10-19T09:00:00Z")   # 1 天
        r = self.cli("retest-pending", "--timestamp=" + NOW, "--window-days=1")
        self.assertIn("FD-g1-0101", r.stdout)

    def test_suspected_and_superseded_excluded(self):
        self.add_finding("FD-g1-0101", "2026-09-01T09:00:00Z", exploitation="suspected")
        self.add_finding("FD-g1-0102", "2026-09-01T09:00:00Z", status="superseded")
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.splitlines()[0].split(chr(9))[0], "#pending=0")

    def test_last_verified_refreshed_by_later_row(self):
        self.add_finding("FD-g1-0101", "2026-09-01T09:00:00Z")
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id="FD-g1-0101", intent_id="INT-g1-0002",
                        title="复验靶 FD-g1-0101", confidence="C1", impact="高",
                        exploitation_status="verified", dedup_key="dk-FD-g1-0101",
                        scope_check="in_scope", description_brief="b",
                        reproducible_steps="s1;s2", affected_asset_id="AST-g1-0002",
                        evidence_ids="EV-g1-0002", status="active",
                        created="2026-10-20T08:00:00Z"))
        self.write("findings.tsv", rows)
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertNotIn("FD-g1-0101", r.stdout)   # 复验刷新后不再过期


class PendingDiscipline(Base):
    def test_timestamp_required(self):
        r = self.cli("retest-pending")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_bad_timestamp_shape(self):
        r = self.cli("retest-pending", "--timestamp=not-a-ts")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_bad_retest_json_fails_closed(self):
        with open(os.path.join(self.g, "retest.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write("{broken")
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_bad_window_value_fails_closed(self):
        with open(os.path.join(self.g, "retest.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"window_days": 0}, f)
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_empty_created_fail_closed_listed(self):
        # created 空/不可解析=按过期收（fail-closed：宁可多复验不漏验）
        self.add_finding("FD-g1-0101", "")
        r = self.cli("retest-pending", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0)
        self.assertIn("FD-g1-0101", r.stdout)


if __name__ == "__main__":
    unittest.main()
