# -*- coding: utf-8 -*-
"""tanyin-canary（批次 2 T4）+ tanyin-budgetctl（批次 2 T5）测试。

纪律：先红后绿；只读复用批次 1 夹具（copytree 到临时目录，绝不改 fixtures/）。
"""
import json, os, re, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CANARY = os.path.join(HERE, "..", "cli", "tanyin-canary")
BUDGET = os.path.join(HERE, "..", "cli", "tanyin-budgetctl")
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TAB = chr(9)


def canary(gd, *args):
    return subprocess.run([PY, CANARY, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def budgetctl(gd, *args):
    return subprocess.run([PY, BUDGET, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def ledger(gd, cmd):
    return subprocess.run([PY, LEDGER, cmd, "--goal-dir", gd], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def tearDown(self):
        self.td.cleanup()

    def deploy(self, seed="seed-alpha"):
        return canary(self.gd, "deploy", "--seed=" + seed)

    def targets(self):
        p = os.path.join(self.gd, "canary", "targets.tsv")
        return [l.split(TAB) for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]

    def timeline(self):
        p = os.path.join(self.gd, "timeline.tsv")
        return [l.split(TAB) for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]

    def budget_append(self, *rows):
        with open(os.path.join(self.gd, "budget.tsv"), "a", encoding="utf-8", newline="") as f:
            for r in rows:
                f.write(TAB.join(r) + chr(10))


class CanaryDeploy(Base):
    def test_seed_determinism(self):
        r = self.deploy("seed-alpha")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        gd2 = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1b"))
        canary(gd2, "deploy", "--seed=seed-alpha")
        gd3 = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1c"))
        canary(gd3, "deploy", "--seed=seed-beta")
        a = open(os.path.join(self.gd, "canary", "targets.tsv"), "rb").read()
        b = open(os.path.join(gd2, "canary", "targets.tsv"), "rb").read()
        c = open(os.path.join(gd3, "canary", "targets.tsv"), "rb").read()
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertIn("canary-deploy", self.timeline()[-1][3])
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_targets_shape(self):
        self.deploy()
        rows = self.targets()
        self.assertEqual(len(rows), 5)
        self.assertEqual([r[0] for r in rows], ["domain"] * 3 + ["ip"] * 2)
        for r in rows[:3]:
            self.assertRegex(r[1], r"^canary\.[0-9a-f]{8}\.tanyin-test$")
        octs = []
        for r in rows[3:]:
            m = re.match(r"^192\.0\.2\.(\d+)$", r[1])
            self.assertIsNotNone(m, r[1])
            octs.append(int(m.group(1)))
        for n in octs:
            self.assertTrue(1 <= n <= 254)
        self.assertNotEqual(octs[0], octs[1])

    def test_deploy_requires_seed(self):
        r = canary(self.gd, "deploy")
        self.assertEqual(r.returncode, 2)

    def test_probe_requires_deploy(self):
        r = canary(self.gd, "probe", "--tier=0")
        self.assertEqual(r.returncode, 2)


class CanaryProbe(Base):
    def setUp(self):
        super().setUp()
        self.deploy()

    def test_probe_bad_tier(self):
        self.assertEqual(canary(self.gd, "probe", "--tier=9").returncode, 2)
        self.assertEqual(canary(self.gd, "probe").returncode, 2)

    def test_tier0_blocks_all(self):
        r = canary(self.gd, "probe", "--tier=0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["status"], "pass")
        self.assertEqual((j["blocked"], j["total"]), (5, 5))
        self.assertTrue(self.timeline()[-1][3].startswith("canary-result"))
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_tier1_blocks_all(self):
        """canary 扩形态（审计 Important #8）：tier1 三形态（裸参数/flag 内嵌/inject）
        零容忍 5/5——每诱饵全形态拦截才计 blocked。"""
        r = canary(self.gd, "probe", "--tier=1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["status"], "pass")
        self.assertEqual((j["blocked"], j["total"]), (5, 5))
        for d in j["detail"]:
            self.assertEqual(sorted(d["forms"]), ["bare", "flag", "inject"], d)
            self.assertEqual(set(d["forms"].values()), {"blocked"}, d)
        # 3 形态 × 5 诱饵 = 15 条 guard-reject 落账
        self.assertEqual(sum(1 for row in self.timeline() if "guard-reject" in row[3]), 15)
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_tier2_zero_tolerance(self):
        """SECW-3：Tier 2 零容忍（出口口径）——hook 模拟器须拦 5/5（裸参数+flag 内嵌
        两形态），宽容三态断言曾掩盖 0/5 事故。"""
        r = canary(self.gd, "probe", "--tier=2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["tier"], 2)
        self.assertEqual(j["status"], "pass")
        self.assertEqual((j["blocked"], j["total"]), (5, 5))
        for d in j["detail"]:
            self.assertEqual(sorted(d["forms"]), ["bare", "flag"], d)
            self.assertEqual(set(d["forms"].values()), {"blocked"}, d)
        self.assertTrue(any(row[3].startswith("canary-result") for row in self.timeline()))
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_tier3_not_deployed(self):
        r = canary(self.gd, "probe", "--tier=3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["status"], "not-deployed")
        self.assertEqual(j["total"], 0)

    def test_tier3_acl_whitelist_assertion(self):
        with open(os.path.join(self.gd, "egress.acl"), "w", encoding="utf-8", newline="\n") as f:
            f.write("allow *.shop.example" + chr(10) + "allow 10.10.0.0/16" + chr(10))
        r = canary(self.gd, "probe", "--tier=3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["status"], "pass")
        self.assertEqual((j["blocked"], j["total"]), (5, 5))
        decoy = self.targets()[0][1]
        with open(os.path.join(self.gd, "egress.acl"), "a", encoding="utf-8", newline="") as f:
            f.write("allow " + decoy + chr(10))
        r2 = canary(self.gd, "probe", "--tier=3")
        self.assertEqual(r2.returncode, 1)
        j2 = json.loads(r2.stdout)
        self.assertEqual(j2["status"], "fail")
        self.assertEqual(j2["blocked"], 4)


class BudgetEnforce(Base):
    def test_enforce_pass(self):
        r = budgetctl(self.gd, "enforce", "--intent-id=INT-g1-0002")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("OK"))
        self.assertIn("INT-g1-0002", r.stdout)

    def test_enforce_goal_exhausted_reject(self):
        self.budget_append(["2026-09-23T04:00:00Z", "0", "60000", "0", "0", "goal", "overrun", "2"])
        r = budgetctl(self.gd, "enforce", "--intent-id=INT-g1-0002")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("budget-exhausted", r.stdout)
        self.assertIn("budgetctl-reject", self.timeline()[-1][3])
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_enforce_intent_share_exhausted_reject(self):
        self.budget_append(["2026-09-23T04:00:00Z", "0", "10000", "0", "0", "INT-g1-0002", "leaf-overrun", "2"])
        r = budgetctl(self.gd, "enforce", "--intent-id=INT-g1-0002")
        self.assertEqual(r.returncode, 1)
        self.assertIn("budget-exhausted", r.stdout)
        self.assertIn("intent", r.stdout)

    def test_enforce_unknown_intent_root_only(self):
        r = budgetctl(self.gd, "enforce", "--intent-id=INT-g1-9999")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("OK"))

    def test_enforce_missing_intent_id(self):
        self.assertEqual(budgetctl(self.gd, "enforce").returncode, 2)

    def test_converge_check_linkage(self):
        self.budget_append(["2026-09-23T04:00:00Z", "0", "60000", "0", "0", "goal", "overrun", "2"])
        r = ledger(self.gd, "converge-check")
        self.assertEqual(r.returncode, 0)
        # 批5 T7 契约随行：verdict 行后增两行可达性计数（#reachable/#unreachable-gaps）
        self.assertEqual(r.stdout.splitlines()[0], "budget-exhausted")


class BudgetRate(Base):
    def test_rate_pass_within_limit(self):
        r = budgetctl(self.gd, "rate", "--now=2026-09-23T02:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)
        self.assertIn("used=25", r.stdout)

    def test_rate_reject_over_limit(self):
        self.budget_append(["2026-09-23T02:05:00Z", "0", "700", "0", "0", "goal", "burst", "2"])
        r = budgetctl(self.gd, "rate", "--now=2026-09-23T02:05:00Z")
        self.assertEqual(r.returncode, 1)
        self.assertIn("rate-limit", r.stdout)
        self.assertIn("used=725", r.stdout)
        self.assertIn("budgetctl-reject", self.timeline()[-1][3])
        self.assertEqual(ledger(self.gd, "verify-chain").returncode, 0)

    def test_rate_old_burst_excluded(self):
        self.budget_append(["2026-09-23T02:05:00Z", "0", "700", "0", "0", "goal", "burst", "2"])
        r = budgetctl(self.gd, "rate", "--now=2026-09-23T02:20:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("used=0", r.stdout)

    def test_rate_left_open_boundary(self):
        rows = [["2026-09-23T01:00:00Z", "12000", "40", "0.2", "0", "goal", "P1 recon", "2"],
                ["2026-09-23T02:00:00Z", "8000", "700", "0.1", "0", "goal", "burst", "2"]]
        with open(os.path.join(self.gd, "budget.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(TAB.join(r) + chr(10) for r in rows))
        r = budgetctl(self.gd, "rate", "--now=2026-09-23T02:10:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("used=0", r.stdout)

    def test_rate_missing_limit_env2(self):
        gp = os.path.join(self.gd, "goals.tsv")
        with open(gp, encoding="utf-8") as f:
            cells = f.read().splitlines()[0].split(TAB)
        cells[8] = ""
        with open(gp, "w", encoding="utf-8", newline="\n") as f:
            f.write(TAB.join(cells) + chr(10))
        self.assertEqual(budgetctl(self.gd, "rate").returncode, 2)


if __name__ == "__main__":
    unittest.main()
