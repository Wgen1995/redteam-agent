# -*- coding: utf-8 -*-
"""功能13补件二·定时复验器 ②复验意图卡（retest-scan）测试。

纪律：过期发现→自动生成复验卡（kind=nday-verify 既有六值；detail 带
[retest:FD-…] 标记+原EV引用+重放命令+原dedup_key）走既有 add-intent 通道
（registry.lookup=goal 写锁既有执法链）进活池（status=candidate 统一排序池）；
优先级字段留空给规划者五因子——不自算分。
python3 -m unittest tests.test_retest_scan
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

    def seed_expired(self, fid="FD-g1-0101", asset="AST-g1-0002", evidence="EV-g1-0002;EV-g1-0003"):
        rows = self.rows("findings.tsv")
        rows.append(row("findings.tsv", id=fid, intent_id="INT-g1-0002",
                        title="过期的验证发现", confidence="C1", impact="高",
                        exploitation_status="verified", dedup_key="AST-g1-0002+CVE-2026-0001",
                        vuln_ref="CVE-2026-0001", scope_check="in_scope",
                        description_brief="b", reproducible_steps="s1;s2",
                        affected_asset_id=asset, evidence_ids=evidence,
                        status="active", created="2026-10-01T09:00:00Z"))
        self.write("findings.tsv", rows)
        ev = self.rows("E-index.tsv")
        for e in ("EV-g1-0002", "EV-g1-0003"):
            ev.append(row("E-index.tsv", id=e, title="EV " + e, source_type="command",
                          observed_at="2026-10-01T08:00:00Z", network_position="internet",
                          repro_command="curl http://x.example/", repro_kind="single",
                          artifact_path="a/" + e, linked_finding=fid,
                          created="2026-10-01T08:00:00Z"))
        self.write("E-index.tsv", ev)

    def latest_intent(self, iid):
        out = None
        for r in self.rows("intents.tsv"):
            if r[0] == iid:
                out = r
        return out

    def retest_intents(self):
        out = {}
        for r in self.rows("intents.tsv"):
            if "[retest:" in r[T["intents.tsv"].index("detail")]:
                out[r[0]] = r   # 事件溯源同 id 取最新行
        return list(out.values())


class ScanCards(Base):
    def test_creates_card_via_add_intent_channel(self):
        self.seed_expired()
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = self.retest_intents()
        self.assertEqual(len(cards), 1)
        c = cards[0]
        I = T["intents.tsv"]
        self.assertEqual(c[I.index("kind")], "nday-verify")            # 既有六值
        self.assertEqual(c[I.index("status")], "candidate")            # 活池（统一排序）
        self.assertEqual(c[I.index("priority")], "")                    # 留空给规划者五因子
        self.assertEqual(c[I.index("origin")], "entity")
        self.assertEqual(c[I.index("engine")], "replay")
        self.assertTrue(c[I.index("budget_share")])
        detail = c[I.index("detail")]
        self.assertIn("[retest:FD-g1-0101]", detail)                   # 复验卡标记
        self.assertIn("EV-g1-0002", detail)                            # 原EV引用
        self.assertIn("EV-g1-0003", detail)
        self.assertIn("tanyin-replay replay --goal-dir", detail)       # 重放命令
        self.assertIn("--id=EV-g1-0002", detail)
        self.assertIn("AST-g1-0002+CVE-2026-0001", detail)             # 原 dedup_key
        # dedup_key=既有 add-intent 铸造形（asset+kind+title）
        self.assertEqual(c[I.index("dedup_key")],
                         "AST-g1-0002+nday-verify+" + c[I.index("title")])
        # 事件入链（走既有 add-intent 通道的旁证）
        self.assertTrue(any(l.startswith("add-intent ") for l in
                            (x[T["timeline.tsv"].index("event")] for x in self.rows("timeline.tsv"))))

    def test_idempotent_while_card_alive(self):
        self.seed_expired()
        self.cli("retest-scan", "--timestamp=" + NOW)
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.retest_intents()), 1)
        self.assertIn("#queued=0", r.stdout)

    def test_next_round_after_card_done(self):
        self.seed_expired()
        self.cli("retest-scan", "--timestamp=" + NOW)
        iid = self.retest_intents()[0][0]
        # 卡终态（done）后：下一轮扫描铸第 2 轮卡（dedup 不撞）
        rows = self.rows("intents.tsv")
        done = list(self.latest_intent(iid))
        done[T["intents.tsv"].index("status")] = "done"
        rows.append(done)
        self.write("intents.tsv", rows)
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = self.retest_intents()
        self.assertEqual(len(cards), 2)
        self.assertIn("#2", cards[1][T["intents.tsv"].index("title")])

    def test_skips_when_finding_not_expired(self):
        self.seed_expired()
        rows = self.rows("findings.tsv")
        rows[-1][T["findings.tsv"].index("created")] = "2026-10-19T09:00:00Z"
        self.write("findings.tsv", rows)
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.retest_intents()), 0)
        self.assertIn("#queued=0", r.stdout)

    def test_skips_out_of_scope_asset(self):
        self.seed_expired(asset="AST-g1-0003")   # 夹具界外资产（in_scope=0）
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.retest_intents()), 0)
        self.assertIn("FD-g1-0101", r.stdout)    # 跳过但留痕


class ScanDiscipline(Base):
    def test_timestamp_required(self):
        r = self.cli("retest-scan")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_header_counts(self):
        self.seed_expired()
        self.seed_expired(fid="FD-g1-0102", evidence="EV-g1-0004")
        r = self.cli("retest-scan", "--timestamp=" + NOW)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        head = r.stdout.splitlines()[0]
        self.assertIn("#expired=2", head)
        self.assertIn("#queued=2", head)


if __name__ == "__main__":
    unittest.main()
