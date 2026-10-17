# -*- coding: utf-8 -*-
"""W2·01P0-2：intents 租约——意图领走带租约（超时回收+双抢互斥）。

来源：docs/reviews/2026-10-17-exceed-review/01-架构专家.md P0-2——
detail 虚拟列加 [owner:W-x][lease:时间戳] 标记（先例=批次 7 T13 [prereq:] 自由文本
承载位）；set-intent-status 执法：租约未过期他主领取=REJECT（防双战士同抢），
租约过期=接管（先落 blocked[reason=lease-expired] 回收行再重授），
blocked[reason=lease-expired] 自动可复活（免 --approval）。

跑法：python3 -m unittest tests.test_intent_lease -v
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger.schemas import TABLES  # noqa: E402

F = TABLES["intents.tsv"]
T0 = "2026-10-20T08:00:00Z"          # 领取钟（场景钟口径，命令入参单源）


def run(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def rows(gd):
    p = os.path.join(gd, "intents.tsv")
    return [l.split("\t") for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]


def latest(gd, iid):
    hit = [r for r in rows(gd) if r[0] == iid]
    return hit[-1] if hit else None


def cell(r, key):
    return r[F.index(key)]


class TestIntentLease(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.d)

    def tearDown(self):
        shutil.rmtree(self.d)

    def _claim(self, owner, ts, lease_min="30", iid="INT-g1-0002"):
        return run(self.d, "set-intent-status", "--id=" + iid, "--status=active",
                   "--owner=" + owner, "--lease-min=" + lease_min, "--timestamp=" + ts)

    # --- 领走落标记 ----------------------------------------------------------

    def test_claim_writes_owner_and_lease_expiry_markers(self):
        r = self._claim("W-1", T0, lease_min="30")
        self.assertEqual(r.returncode, 0, r.stderr)
        row = latest(self.d, "INT-g1-0002")
        self.assertEqual(cell(row, "status"), "active")
        self.assertIn("[owner:W-1]", cell(row, "detail"))
        self.assertIn("[lease:2026-10-20T08:30:00Z]", cell(row, "detail"))

    def test_claim_without_owner_keeps_detail_untouched(self):
        r = run(self.d, "set-intent-status", "--id=INT-g1-0002", "--status=active",
                "--timestamp=" + T0)
        self.assertEqual(r.returncode, 0, r.stderr)
        row = latest(self.d, "INT-g1-0002")
        self.assertNotIn("[owner:", cell(row, "detail"))
        self.assertNotIn("[lease:", cell(row, "detail"))

    # --- 双抢互斥 ------------------------------------------------------------

    def test_double_grab_live_lease_rejected(self):
        self.assertEqual(self._claim("W-1", T0, lease_min="30").returncode, 0)
        r = self._claim("W-2", "2026-10-20T08:10:00Z")   # 10 分钟后租约仍活
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)
        self.assertIn("租约", r.stderr)
        self.assertEqual(cell(latest(self.d, "INT-g1-0002"), "status"), "active")
        self.assertIn("[owner:W-1]", cell(latest(self.d, "INT-g1-0002"), "detail"))

    def test_same_owner_reclaim_live_lease_rejected(self):
        self.assertEqual(self._claim("W-1", T0, lease_min="30").returncode, 0)
        r = self._claim("W-1", "2026-10-20T08:05:00Z")   # 同主重复领取
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    # --- 超时回收 ------------------------------------------------------------

    def test_expired_lease_takeover_lands_blocked_then_regrants(self):
        self.assertEqual(self._claim("W-1", T0, lease_min="5").returncode, 0)
        takeover_ts = "2026-10-20T08:10:00Z"              # 5 分钟租约已过
        r = self._claim("W-2", takeover_ts, lease_min="30")
        self.assertEqual(r.returncode, 0, r.stderr)
        seq = [r_ for r_ in rows(self.d) if r_[0] == "INT-g1-0002"]
        # 回收行：blocked + reason=lease-expired（时间戳=接管钟）
        mid = seq[-2]
        self.assertEqual(cell(mid, "status"), "blocked")
        self.assertEqual(cell(mid, "reason"), "lease-expired")
        self.assertEqual(cell(mid, "created"), takeover_ts)
        # 重授行：active + 新主新租约
        fin = seq[-1]
        self.assertEqual(cell(fin, "status"), "active")
        self.assertIn("[owner:W-2]", cell(fin, "detail"))
        self.assertIn("[lease:2026-10-20T08:40:00Z]", cell(fin, "detail"))
        self.assertNotIn("[owner:W-1]", cell(fin, "detail"))

    def test_expired_blocked_auto_revives_without_approval(self):
        # 回收路径二（非接管钟内）：active → blocked(lease-expired) 落定后，
        # 任意战士复活免 --approval（自动可复活律）
        self.assertEqual(self._claim("W-1", T0, lease_min="5").returncode, 0)
        r = run(self.d, "set-intent-status", "--id=INT-g1-0002", "--status=blocked",
                "--reason=lease-expired", "--timestamp=2026-10-20T08:12:00Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self._claim("W-2", "2026-10-20T08:20:00Z", lease_min="30")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[owner:W-2]", cell(latest(self.d, "INT-g1-0002"), "detail"))

    def test_normal_blocked_still_requires_approval(self):
        # 回归钉：非 lease-expired 的 blocked 复活仍须 --approval（既有执法不松）
        self.assertEqual(run(self.d, "set-intent-status", "--id=INT-g1-0002",
                             "--status=active", "--timestamp=" + T0).returncode, 0)
        self.assertEqual(run(self.d, "set-intent-status", "--id=INT-g1-0002",
                             "--status=blocked", "--reason=证据不足",
                             "--timestamp=" + T0).returncode, 0)
        r = run(self.d, "set-intent-status", "--id=INT-g1-0002", "--status=active",
                "--timestamp=" + T0)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    # --- 参数执法 ------------------------------------------------------------

    def test_bad_owner_token_rejected(self):
        r = self._claim("W 1]bad", T0)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    def test_bad_lease_min_rejected(self):
        r = self._claim("W-1", T0, lease_min="abc")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)

    # --- 租约审计（查询面） ----------------------------------------------------

    def test_lease_audit_lists_held_and_expired(self):
        self.assertEqual(self._claim("W-1", T0, lease_min="30").returncode, 0)
        r = run(self.d, "intent-lease", "--timestamp=2026-10-20T08:10:00Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("INT-g1-0002\tW-1\t2026-10-20T08:30:00Z\theld", r.stdout)
        # 过期钟点：expired 判定 + 退出码 1（可回收信号）
        r2 = run(self.d, "intent-lease", "--timestamp=2026-10-20T08:31:00Z")
        self.assertEqual(r2.returncode, 1)
        self.assertIn("INT-g1-0002\tW-1\t2026-10-20T08:30:00Z\texpired", r2.stdout)


if __name__ == "__main__":
    unittest.main()
