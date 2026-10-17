# -*- coding: utf-8 -*-
"""W2·01P0-4：多战执法面——并发战资源仲裁（注册表式：预算帽+端口冲突检测）。

来源：docs/reviews/2026-10-17-exceed-review/01-架构专家.md P0-4
「战斗注册表（battle home 侧 registry）+全局并发闸+每战资源帽」——本测试钉
CLI 侧仲裁核（webui launch/stop 接线另见 test_v09a_webui 回归）。

跑法：python3 -m unittest tests.test_battle_registry -v
"""
import json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import battle_registry as br  # noqa: E402


def alive_pids(*pids):
    return lambda p: p in set(pids)


class TestBattleRegistry(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def reg_path(self):
        return os.path.join(self.root, br.REGISTRY_NAME)

    # --- 预算仲裁 ------------------------------------------------------------

    def test_budget_within_cap_admitted(self):
        v1 = br.admit(self.root, "battle-1", budget_usd=60.0, pid=111,
                      cap_budget_usd=100.0, pid_alive=alive_pids(111))
        self.assertTrue(v1["allowed"], v1)
        v2 = br.admit(self.root, "battle-2", budget_usd=40.0, pid=112,
                      cap_budget_usd=100.0, pid_alive=alive_pids(111, 112))
        self.assertTrue(v2["allowed"], v2)     # 60+40=100 恰在帽内

    def test_budget_over_cap_rejected_not_registered(self):
        br.admit(self.root, "battle-1", budget_usd=60.0, pid=111,
                 cap_budget_usd=100.0, pid_alive=alive_pids(111))
        v = br.admit(self.root, "battle-2", budget_usd=50.0, pid=112,
                     cap_budget_usd=100.0, pid_alive=alive_pids(111, 112))
        self.assertFalse(v["allowed"])
        self.assertEqual(v["reason"], "budget-cap")
        self.assertIn("110", json.dumps(v))     # 数学披露（60+50=110 > 100）
        snap = br.snapshot(self.root)
        self.assertEqual([e["battle"] for e in snap["entries"]], ["battle-1"])
        self.assertEqual(snap["budget_used"], 60.0)

    def test_release_frees_budget_for_next(self):
        br.admit(self.root, "battle-1", budget_usd=60.0, pid=111,
                 pid_alive=alive_pids(111))
        freed = br.release(self.root, "battle-1")
        self.assertEqual(freed["battle"], "battle-1")
        self.assertEqual(freed["freed_budget_usd"], 60.0)
        v = br.admit(self.root, "battle-2", budget_usd=80.0, pid=112,
                     cap_budget_usd=100.0, pid_alive=alive_pids(112))
        self.assertTrue(v["allowed"], v)

    def test_no_cap_disables_budget_gate_but_still_registers(self):
        v1 = br.admit(self.root, "battle-1", budget_usd=1e9, pid=111,
                      pid_alive=alive_pids(111))
        v2 = br.admit(self.root, "battle-2", budget_usd=1e9, pid=112,
                      pid_alive=alive_pids(111, 112))
        self.assertTrue(v1["allowed"] and v2["allowed"])
        self.assertEqual(br.snapshot(self.root)["budget_used"], 2e9)

    # --- 端口冲突 ------------------------------------------------------------

    def test_port_conflict_rejected(self):
        br.admit(self.root, "battle-1", ports=(9101, 9102), pid=111,
                 pid_alive=alive_pids(111))
        v = br.admit(self.root, "battle-2", ports=(9102, 9103), pid=112,
                     pid_alive=alive_pids(111, 112))
        self.assertFalse(v["allowed"])
        self.assertEqual(v["reason"], "port-conflict")
        self.assertIn(9102, v["conflict_ports"])
        v2 = br.admit(self.root, "battle-2", ports=(9103,), pid=112,
                      pid_alive=alive_pids(111, 112))
        self.assertTrue(v2["allowed"], v2)

    def test_forbidden_ports_rejected(self):
        v = br.admit(self.root, "battle-1", ports=(8900,), pid=111,
                     forbid_ports=(8900, 3000, 8787, 8443),
                     pid_alive=alive_pids(111))
        self.assertFalse(v["allowed"])
        self.assertEqual(v["reason"], "port-forbidden")
        self.assertIn(8900, v["conflict_ports"])

    def test_claim_ports_extends_live_entry(self):
        br.admit(self.root, "battle-1", ports=(9101,), pid=111,
                 pid_alive=alive_pids(111))
        r = br.claim_ports(self.root, "battle-1", (9102,),
                           pid_alive=alive_pids(111))
        self.assertTrue(r["allowed"], r)
        v = br.admit(self.root, "battle-2", ports=(9102,), pid=112,
                     pid_alive=alive_pids(111, 112))
        self.assertFalse(v["allowed"])
        self.assertEqual(v["reason"], "port-conflict")

    # --- 双点火互斥与死 pid 回收 ----------------------------------------------

    def test_duplicate_live_battle_rejected(self):
        br.admit(self.root, "battle-1", pid=111, pid_alive=alive_pids(111))
        v = br.admit(self.root, "battle-1", pid=222,
                     pid_alive=alive_pids(111, 222))
        self.assertFalse(v["allowed"])
        self.assertEqual(v["reason"], "already-registered")

    def test_dead_pid_reaped_frees_budget_and_ports(self):
        br.admit(self.root, "battle-1", budget_usd=90.0, ports=(9101,), pid=111,
                 pid_alive=alive_pids(111))
        # pid 111 已死：仲裁前回收——预算与端口全释放
        v = br.admit(self.root, "battle-2", budget_usd=90.0, ports=(9101,), pid=222,
                     cap_budget_usd=100.0, pid_alive=alive_pids(222))
        self.assertTrue(v["allowed"], v)
        self.assertEqual([e["battle"] for e in br.snapshot(self.root)["entries"]],
                         ["battle-2"])

    # --- 申报执法 ------------------------------------------------------------

    def test_negative_budget_rejected(self):
        """负预算申报=调用方程序错（负数入册会压低 budget_used——仲裁面禁洞）。"""
        with self.assertRaises(ValueError):
            br.admit(self.root, "battle-1", budget_usd=-5.0,
                     pid_alive=alive_pids(111))

    def test_non_finite_budget_rejected(self):
        """NaN/inf 申报=ValueError（NaN 恒假比较可穿一切帽——fail-closed）。"""
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                br.admit(self.root, "battle-1", budget_usd=bad,
                         pid_alive=alive_pids(111))

    # --- 注册表纪律 -----------------------------------------------------------

    def test_bad_battle_name_raises(self):
        with self.assertRaises(ValueError):
            br.admit(self.root, "foo", pid=111, pid_alive=alive_pids(111))

    def test_corrupt_registry_fails_closed(self):
        with open(self.reg_path(), "w", encoding="utf-8") as f:
            f.write("{not-json")
        with self.assertRaises(ValueError):
            br.admit(self.root, "battle-1", pid=111, pid_alive=alive_pids(111))

    def test_release_missing_battle_returns_none(self):
        self.assertIsNone(br.release(self.root, "battle-9"))

    def test_snapshot_shape(self):
        br.admit(self.root, "battle-3", budget_usd=12.5, ports=(9103,), pid=303,
                 pid_alive=alive_pids(303))
        snap = br.snapshot(self.root)
        self.assertEqual(snap["schema_version"], 1)
        self.assertEqual(len(snap["entries"]), 1)
        e = snap["entries"][0]
        self.assertEqual(e["battle"], "battle-3")
        self.assertEqual(e["budget_usd"], 12.5)
        self.assertEqual(e["ports"], [9103])
        self.assertEqual(snap["budget_used"], 12.5)


if __name__ == "__main__":
    unittest.main()
