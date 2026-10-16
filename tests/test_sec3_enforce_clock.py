# -*- coding: utf-8 -*-
"""SEC-1 舰 S3（2026-10-15 v0.9.6 执法面升权批）：执法钟防时间旅行。

依据 plan SEC-1 舰节 + review 02-security-enforcement.md S3：
rate/预算窗时钟锚原=战士自报 --timestamp（enforce.rate_window(now=parse_ts(ts))，
guard:186）——谎报未来一个窗长即可让旧请求滑出 (now-w, now]。

新锚（计划口径）：账本 seq 单调 + 链上时间戳（timeline.tsv 追加单链的最大
链上时刻）为执法钟；自报 --timestamp 降参考；战斗内回拨/前跳超阈值
（TIME_TRAVEL_TOLERANCE）=REJECT 上账（guard-reject time-travel 落 timeline，
REJECT 行时戳用链上钟——不因拒绝行污染链尖）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
GUARD = os.path.join(CLI, "tanyin-guard")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable
TAB = chr(9)

sys.path.insert(0, CLI)
from ledger import core, enforce  # noqa: E402

# G-g1 夹具链尖（timeline.tsv 最大链上时刻）=2026-09-23T03:05:00Z
CHAIN_TIP = "2026-09-23T03:05:00Z"
NEAR = "2026-09-23T03:10:00Z"      # 链尖+5min：正常推进
FAR_BACK = "2026-08-01T00:00:00Z"  # 回拨 ~53 天 > 容差
FAR_FWD = "2026-12-15T00:00:00Z"   # 前跳 ~83 天 > 容差


def _goal_dir(case, name="G-g1"):
    td = tempfile.TemporaryDirectory()
    case.addCleanup(td.cleanup)
    return shutil.copytree(FIX, os.path.join(td.name, name))


def _guard(gd, ts, *cmd):
    return subprocess.run(
        [PY, GUARD, "exec", "--goal-dir", gd, "--timestamp=" + ts, "--"] + list(cmd),
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def _timeline(gd):
    with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
        return f.read()


def _budget_append(gd, ts, requests):
    with open(os.path.join(gd, "budget.tsv"), "a", encoding="utf-8", newline=chr(10)) as f:
        f.write(TAB.join([ts, "0", str(requests), "0", "0", "goal", "sec3", "2"]) + chr(10))


class TestChainClockUnit(unittest.TestCase):
    def _session(self, timeline=(), budget=()):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        gd = td.name
        if timeline:
            with open(os.path.join(gd, "timeline.tsv"), "w", encoding="utf-8",
                      newline=chr(10)) as f:
                for ts in timeline:
                    f.write(TAB.join([ts, "t", "P0", "evt", "", "0" * 64,
                                      "0" * 64, "2"]) + chr(10))
        if budget:
            with open(os.path.join(gd, "budget.tsv"), "w", encoding="utf-8",
                      newline=chr(10)) as f:
                for ts, req in budget:
                    f.write(TAB.join([ts, "0", str(req), "0", "0", "goal", "s", "2"]) + chr(10))
        return core.Session(gd)

    def test_chain_time_is_max_timeline_stamp(self):
        got = enforce.chain_time(self._session(
            timeline=["2026-09-23T01:00:00Z", "2026-09-23T03:05:00Z",
                      "2026-09-23T02:00:00Z"]))
        self.assertIsNotNone(got)
        epoch, iso = got
        self.assertEqual(iso, "2026-09-23T03:05:00Z")
        self.assertEqual(epoch, enforce.parse_ts("2026-09-23T03:05:00Z"))

    def test_chain_time_empty_ledger_none(self):
        self.assertIsNone(enforce.chain_time(self._session(budget=[
            ("2026-09-23T02:00:00Z", 5)])))

    def test_time_travel_verdict(self):
        chain = enforce.parse_ts(CHAIN_TIP)
        self.assertEqual(enforce.time_travel_verdict(
            enforce.parse_ts("2026-09-23T02:06:00Z"), chain), None,
            "59min 回拨在容差内（op1 既有语义）")
        self.assertEqual(enforce.time_travel_verdict(
            enforce.parse_ts(FAR_BACK), chain), "rollback")
        self.assertEqual(enforce.time_travel_verdict(
            enforce.parse_ts(FAR_FWD), chain), "jump")
        self.assertIsNone(enforce.time_travel_verdict(
            enforce.parse_ts(FAR_BACK), None), "空账本=首戳立锚不判")

    def test_enforcement_anchor_clamped_to_chain(self):
        chain = enforce.parse_ts(CHAIN_TIP)
        tol = enforce.TIME_TRAVEL_TOLERANCE
        self.assertEqual(enforce.enforcement_anchor(chain + 5, chain), chain + 5)
        self.assertEqual(enforce.enforcement_anchor(chain - tol - 9999, chain), chain - tol)
        self.assertEqual(enforce.enforcement_anchor(chain + tol + 9999, chain), chain + tol)
        self.assertEqual(enforce.enforcement_anchor(12345.0, None), 12345.0)


class TestGuardTimeTravel(unittest.TestCase):
    def test_rollback_rejected_and_recorded(self):
        gd = _goal_dir(self)
        r = _guard(gd, FAR_BACK, PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("time-travel", r.stdout)
        self.assertIn("rollback", r.stdout)
        tl = _timeline(gd)
        self.assertIn("guard-reject time-travel mode=rollback", tl)
        ok, _line = core.Session(gd).verify_chain()
        self.assertTrue(ok, "time-travel REJECT 落账后链须完整")

    def test_forward_jump_rejected_and_recorded(self):
        gd = _goal_dir(self)
        r = _guard(gd, FAR_FWD, PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("time-travel", r.stdout)
        self.assertIn("jump", r.stdout)
        self.assertIn("guard-reject time-travel mode=jump", _timeline(gd))

    def test_reject_row_uses_chain_clock_not_claimed(self):
        """REJECT 行时戳=链上钟：拒绝行不得把链尖推向谎报时刻。"""
        gd = _goal_dir(self)
        _guard(gd, FAR_FWD, PY, "-c", "pass", "ping", "api.shop.example")
        s = core.Session(gd)
        got = enforce.chain_time(s)
        self.assertEqual(got[1], CHAIN_TIP, "前跳 REJECT 后链尖须仍在原时刻")

    def test_nearby_timestamp_passes_clock_gate(self):
        gd = _goal_dir(self)
        r = _guard(gd, NEAR, PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("time-travel", r.stdout)
        self.assertIn("request-ticket", _timeline(gd).splitlines()[-1])

    def test_rate_gate_semantics_preserved_within_tolerance(self):
        """op1 语义回归：容差内自报时戳仍作窗锚参考——超窗照拒。"""
        gd = _goal_dir(self)
        _budget_append(gd, "2026-09-23T02:05:00Z", 700)
        r = _guard(gd, "2026-09-23T02:06:00Z", PY, "-c", "pass", "ping", "api.shop.example")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("rate-limit", r.stdout)
        self.assertIn("used=725", r.stdout)


if __name__ == "__main__":
    unittest.main()
