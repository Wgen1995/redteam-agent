# -*- coding: utf-8 -*-
"""功能24a·外部执行后端③：任务包序列化（TDD 红测试先行）。

设计定稿 §3「会话映射」：意图卡 → 任务包（goal+scope+预算+红线序列化）→
后端会话。任务包=派给外部肌肉的唯一公文：外部后端只拿到它该拿的（目标、
范围、预算、红线、输出契约），拿不到账本全貌（最小披露律）。

契约：
- build(goal_dir, intent_id, task_id)：从账本（只读 Session）组包——
  goal 行（目标/对象/速率窗/有效期）、scope include 行、预算三段
  （token;requests;hours，K/M/G 后缀）× 意图 budget_share 分摊、红线
  （rate_limit/window/valid_until/guard_tier）、意图本体、输出契约
  （facts/findings 字段与枚举——归一入账的对面）。
- serialize()=确定性 JSON（sort_keys，可回放比对）。
- 预算段解析 _seg：40k→40000、2M→2e6、1G→1e9；缺段/坏段=fail-loud。

跑法：python3 -m unittest tests.test_backends_taskpack -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from backends import taskpack  # noqa: E402


class BudgetParseCase(unittest.TestCase):
    """预算三段解析（K/M/G 后缀=既有 _seg_int 同语义）。"""

    def test_plain_integers(self):
        self.assertEqual(taskpack.parse_budget("50000;100;40"),
                         (50000, 100, 40))

    def test_kmg_suffixes(self):
        self.assertEqual(taskpack.parse_budget("2M;10k;1G"),
                         (2 * 1000 * 1000, 10 * 1000, 10 ** 9))

    def test_lowercase_suffix(self):
        self.assertEqual(taskpack.parse_budget("40k;1m;2g"), (40000, 1000000, 2 * 10 ** 9))

    def test_missing_segment_fails_loud(self):
        with self.assertRaises(ValueError):
            taskpack.parse_budget("2M;50000")

    def test_garbage_segment_fails_loud(self):
        with self.assertRaises(ValueError):
            taskpack.parse_budget("2M;abc;40")


class TaskPackCase(unittest.TestCase):
    def setUp(self):
        self.gd = shutil.copytree(FIX, tempfile.mkdtemp() + "/G-t")
        self.addCleanup(shutil.rmtree, self.gd, ignore_errors=True)

    def _build(self, intent_id="INT-g1-0002", task_id="T-24a-1"):
        return taskpack.TaskPackage.build(self.gd, intent_id, task_id)

    def test_goal_block_from_ledger(self):
        p = self._build().to_dict()
        self.assertEqual(p["goal"]["id"], "G-g1-0001")
        self.assertEqual(p["goal"]["target"], "shop.example")
        self.assertEqual(p["goal"]["objective"], "授权渗透：商城内网分区")

    def test_scope_only_includes(self):
        p = self._build().to_dict()
        matchers = [s["matcher"] for s in p["scope"]]
        self.assertIn("*.shop.example", matchers)
        self.assertIn("10.10.0.0/16", matchers)
        # account 授权面随行（外部肌肉知道能用什么身份）
        acct = [s for s in p["scope"] if s["matcher"] == "10.10.0.0/16"][0]
        self.assertEqual(acct["account"], "admin;operator")

    def test_budget_parsed_and_shared(self):
        p = self._build().to_dict()   # INT-g1-0002 budget_share=0.2
        self.assertEqual(p["budget"]["token_cap"], 400000)   # 2M × 0.2
        self.assertEqual(p["budget"]["requests_cap"], 10000)  # 50000 × 0.2
        self.assertEqual(p["budget"]["hours_cap"], 8)          # 40 × 0.2 取整

    def test_redlines_block(self):
        p = self._build().to_dict()
        self.assertEqual(p["redlines"]["rate_limit"], "600/10m")
        self.assertEqual(p["redlines"]["window"], "09:00-19:00")
        self.assertEqual(p["redlines"]["valid_until"], "2026-09-30")
        self.assertEqual(p["redlines"]["guard_tier"], "T3")

    def test_intent_block(self):
        p = self._build().to_dict()
        self.assertEqual(p["intent"]["id"], "INT-g1-0002")
        self.assertEqual(p["intent"]["title"], "admin 面板未授权访问")
        self.assertEqual(p["intent"]["engine"], "web-blackbox")

    def test_task_id_and_protocol_version(self):
        p = self._build().to_dict()
        self.assertEqual(p["task_id"], "T-24a-1")
        self.assertEqual(p["v"], 1)

    def test_output_contract_carries_ingest_enums(self):
        """输出契约=归一入账的对面：外部必须按账本枚举产出。"""
        p = self._build().to_dict()
        oc = p["output_contract"]
        self.assertIn("facts", oc)
        self.assertIn("findings", oc)
        f = oc["findings"]
        self.assertIn("C1", f["confidence"])
        self.assertIn("verified", f["exploitation_status"])
        self.assertIn("in_scope", f["scope_check"])
        self.assertIn("高", f["impact"])
        self.assertIn("reproducible_steps", f["required"])

    def test_serialize_deterministic_roundtrip(self):
        p1 = self._build()
        p2 = self._build()
        self.assertEqual(p1.serialize(), p2.serialize())
        back = json.loads(p1.serialize())
        self.assertEqual(back["task_id"], "T-24a-1")

    def test_unknown_intent_fails_loud(self):
        with self.assertRaises(ValueError):
            self._build(intent_id="INT-nope-9999")

    def test_minimal_disclosure_no_secrets(self):
        """任务包不带凭据真值/哈希/auth_doc 内路径（最小披露律）。"""
        raw = self._build().serialize()
        self.assertNotIn("auth_sha256", raw)
        self.assertNotIn("{{vault:", raw)
        self.assertNotIn("emergency_contact", raw)


if __name__ == "__main__":
    unittest.main()
