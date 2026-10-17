# -*- coding: utf-8 -*-
"""W3-P1-1①：sqlmap 受控档参数墙——只读检测档的单测（docs/reviews/2026-10-17
-exceed-review/03-渗透工作流专家.md P1-1「sqlmap OSD 受控档位」引擎面）。

墙五件（全部引擎侧机械执法，适配器 argv 只由白名单旋钮拼装、无透传）：
1 --delay 强制（缺省注入 1s；<0.5 或 >60=墙拒——防锤击下限锁定）
2 禁碰端口（8900/3000/8787/8443——交战纪律 FORBIDDEN_PORTS 同源）
3 --level≤3/--risk≤2 受控顶（guard deny-list 已拦 --level=5/--risk=3，引擎侧更紧）
4 限库限表（-D 须在 --dbs 白名单；-T 须伴 -D 且在 --tables 白名单）
5 数据面旗标结构性不可达（--dump/--os-shell 等写/外带面永不进 argv）
"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ADAPTER = os.path.join(ROOT, "engines", "sqlmap", "adapter.py")
TGT = "http://target.example/items.php"


class SqlmapWallBase(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def plan(self, *extra):
        # 目标可被 extra 覆盖（argv 契约=首个 --key 生效，故此处按需注入缺省目标）
        toks = [sys.executable, ADAPTER, "--intent-id", "INT-g1-0300",
                "--out-dir", self.out, "--plan"]
        if not any(str(x).startswith("--target") for x in extra):
            toks += ["--target", TGT]
        return subprocess.run(toks + list(extra),
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def plan_json(self, *extra):
        r = self.plan(*extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout.strip().splitlines()[-1])


class TestDelayWall(SqlmapWallBase):
    """--delay 强制：缺省注入；下限 0.5s；上限 60s。"""

    def test_delay_injected_by_default(self):
        p = self.plan_json()
        self.assertEqual(p["wall"], "pass", p)
        self.assertIn("--delay=1", p["argv"], "缺省 --delay=1 必须强制在场")

    def test_delay_floor_enforced(self):
        p = self.plan_json("--delay", "0.05")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("delay", p["reason"])
        self.assertIn("0.5", p["reason"], "须出示下限 0.5s")

    def test_delay_ceiling_enforced(self):
        p = self.plan_json("--delay=999")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("delay", p["reason"])

    def test_delay_explicit_passes(self):
        p = self.plan_json("--delay", "2")
        self.assertEqual(p["wall"], "pass", p)
        self.assertIn("--delay=2", p["argv"])


class TestPortWall(SqlmapWallBase):
    """交战纪律禁碰端口——目标 URL 命中即墙拒（fail-closed）。"""

    def test_forbidden_port_blocked(self):
        p = self.plan_json("--target", "http://127.0.0.1:8900/app")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("8900", p["reason"])

    def test_forbidden_port_8443_blocked(self):
        p = self.plan_json("--target", "https://intra.example:8443/")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("8443", p["reason"])


class TestCeilingWall(SqlmapWallBase):
    """/--risk 受控顶：level≤3、risk≤2（越顶=墙拒，非审批可救）。"""

    def test_level_over_ceiling_blocked(self):
        p = self.plan_json("--level=4")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("level", p["reason"].lower())

    def test_risk_over_ceiling_blocked(self):
        p = self.plan_json("--risk=3")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("risk", p["reason"].lower())

    def test_level_floor_no_approval_needed(self):
        p = self.plan_json("--level", "1", "--risk", "1")
        self.assertEqual(p["wall"], "pass", p)
        self.assertFalse(p["needs_approval"], "受控档位地槛（1/1）无须 L3")


class TestDbTableWhitelist(SqlmapWallBase):
    """限库限表：-D 须在 --dbs；-T 须伴 -D 且在 --tables。"""

    def test_db_not_in_whitelist_blocked(self):
        p = self.plan_json("--database", "mysql", "--dbs", "app,legacy")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("库白名单", p["reason"])

    def test_db_in_whitelist_reaches_approval_gate(self):
        """白名单通过→下一门=L3 审批（缺省拒），不报库白名单错。"""
        p = self.plan_json("--database", "app", "--dbs", "app,legacy")
        self.assertEqual(p["wall"], "blocked")
        self.assertNotIn("库白名单", p["reason"])
        self.assertTrue(p["needs_approval"])

    def test_table_without_db_blocked(self):
        p = self.plan_json("--table", "users", "--tables", "users")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("database", p["reason"].lower())

    def test_table_not_in_whitelist_blocked(self):
        p = self.plan_json("--database", "app", "--dbs", "app",
                           "--table", "admin", "--tables", "users,posts")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("表白名单", p["reason"])

    def test_table_in_whitelist_reaches_approval_gate(self):
        p = self.plan_json("--database", "app", "--dbs", "app",
                           "--table", "users", "--tables", "users,posts")
        self.assertEqual(p["wall"], "blocked")
        self.assertNotIn("表白名单", p["reason"])
        self.assertTrue(p["needs_approval"])

    def test_empty_whitelist_denies_any_db(self):
        """缺省零白名单=零库可碰（fail-closed，非静默放开）。"""
        p = self.plan_json("--database", "anything")
        self.assertEqual(p["wall"], "blocked")
        self.assertIn("库白名单", p["reason"])


class TestReadonlyProfile(SqlmapWallBase):
    """只读检测档：argv 只由白名单旋钮拼装，写/外带面旗标结构性不可达。"""

    def test_base_argv_shape(self):
        p = self.plan_json()
        self.assertEqual(p["wall"], "pass", p)
        joined = " ".join(p["argv"])
        for tok in ("--batch", "--delay=1", "--threads=1"):
            self.assertIn(tok, joined, "受控基座参数必须在场: " + tok)
        self.assertIn("-u", p["argv"])

    def test_dump_flag_structurally_unreachable(self):
        """未知旗标不透传：--dump 进不了 argv（墙后零残留）。"""
        p = self.plan_json("--dump", "--os-shell")
        joined = " ".join(p["argv"])
        self.assertNotIn("--dump", joined)
        self.assertNotIn("--os-shell", joined)

    def test_param_knob_maps_to_p(self):
        p = self.plan_json("--param", "id")
        self.assertEqual(p["wall"], "pass", p)
        i = p["argv"].index("-p")
        self.assertEqual(p["argv"][i + 1], "id")

    def test_command_hash_deterministic(self):
        a = self.plan_json()
        b = self.plan_json("--param", "id")
        self.assertNotEqual(a["command_hash"], b["command_hash"],
                            "hash 须随计划命令变化（L3 逐条审批锚）")


if __name__ == "__main__":
    unittest.main()
