# -*- coding: utf-8 -*-
"""功能6 TDD⑤: 业务流作弊考卷种子(evals/gt/battlefields/range-bizflow-v1.json)——先失败测试。

种子形照 range-chain-v1.json(chain-gt);三类: 改价/优惠券重用/取消后发货
(设计§考卷: 补业务流作弊种子入 range 考卷下一版)。
纪律:
- 种子惰性: 未注册 gt-index(注册即触发 gt_verify 实跑锚——bizflow GT/夹具未植,
  半注册=评测棘轮假失败掩真回归);激活=下一版 GT 植入+夹具在案+注册三步齐;
- gt_ref 口径: 共享环引用现存 session-GT 条目(weakpass-01);新环引用
  pending_gt 声明的待植条目(bizflow-*),且不得与现存 GT 幂等混写;
- 守卫同源: verify_cmd 逐条过 gt_verify.check_verify_cmd(只读 grep/test 段式);
- 环号全局唯一: 与 zl-chain-v1/range-chain-v1 现存 id 无碰撞。
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GT_DIR = os.path.join(ROOT, "evals", "gt")
SEED = os.path.join(GT_DIR, "battlefields", "range-bizflow-v1.json")
INDEX = os.path.join(GT_DIR, "gt-index.tsv")

sys.path.insert(0, GT_DIR)
import gt_verify  # noqa: E402

REQUIRED_CHAIN_FIELDS = gt_verify.REQUIRED_CHAIN_FIELDS
REQUIRED_STEP_FIELDS = gt_verify.REQUIRED_STEP_FIELDS


def _session_gt_ids():
    with open(os.path.join(ROOT, "tests", "range", "ground-truth.json"),
              encoding="utf-8") as f:
        return {e.get("id") for e in json.load(f).get("planted", [])}


def _existing_chain_ids():
    seen = set()
    for name in ("zl-chain-v1.json", "range-chain-v1.json"):
        with open(os.path.join(GT_DIR, "battlefields", name), encoding="utf-8") as f:
            doc = json.load(f)
        for c in doc.get("chains", []):
            seen.add(c["id"])
            for s in c.get("steps", []):
                seen.add(s["id"])
    return seen


class TestSeedShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SEED, encoding="utf-8") as f:
            cls.doc = json.load(f)

    def test_battlefield_header(self):
        d = self.doc
        self.assertEqual(d["battlefield"], "range-bizflow-v1")
        self.assertEqual(d["kind"], "chain-gt")
        self.assertEqual(d["status"], "seed", "种子态显形——激活前不入评测")
        self.assertEqual(d["session_gt"], "tests/range/ground-truth.json")
        self.assertTrue(d.get("activates_when"), "激活条件写死(三步: GT 植入/夹具/注册)")

    def test_three_cheat_classes_present(self):
        classes = {c["class"] for c in self.doc["chains"]}
        self.assertEqual(classes, {"bizflow-price", "bizflow-coupon", "bizflow-shipcancel"},
                         "改价/优惠券重用/取消后发货三类齐(设计§考卷)")

    def test_chain_fields_complete(self):
        for c in self.doc["chains"]:
            miss = [k for k in REQUIRED_CHAIN_FIELDS if not c.get(k)]
            self.assertEqual(miss, [], c.get("id"))
            self.assertEqual(c["polarity"], "pos")
            self.assertEqual(c["status"], "open")
            self.assertGreaterEqual(len(c["steps"]), 2)

    def test_step_fields_and_orders(self):
        for c in self.doc["chains"]:
            self.assertEqual([s["order"] for s in c["steps"]],
                             list(range(1, len(c["steps"]) + 1)),
                             "环序 1..N 连续(gt_verify 同规)")
            for s in c["steps"]:
                miss = [k for k in REQUIRED_STEP_FIELDS if not s.get(k)]
                self.assertEqual(miss, [], s.get("id"))

    def test_step_ids_globally_unique(self):
        existing = _existing_chain_ids()
        seen = set()
        for c in self.doc["chains"]:
            for s in c["steps"]:
                self.assertNotIn(s["id"], existing, "与现存战场环号碰撞: " + s["id"])
                self.assertNotIn(s["id"], seen, "种子内环号重复: " + s["id"])
                seen.add(s["id"])

    def test_gt_ref_discipline(self):
        gt_ids = _session_gt_ids()
        pending = set(self.doc.get("pending_gt", []))
        self.assertTrue(pending, "待植 GT 条目显式声明(pending_gt)")
        self.assertFalse(pending & gt_ids, "pending 条目不得与现存 GT 幂等混写")
        for c in self.doc["chains"]:
            for s in c["steps"]:
                ref = s.get("gt_ref", "")
                self.assertTrue(ref, "会话链步必带 gt_ref(gt_verify 同规)")
                self.assertIn(ref, gt_ids | pending,
                              "%s 的 gt_ref 须落在现存 GT 或 pending_gt: %s"
                              % (s["id"], ref))

    def test_verify_cmds_guard_safe(self):
        for c in self.doc["chains"]:
            for s in c["steps"]:
                ok, why = gt_verify.check_verify_cmd(s["verify_cmd"])
                self.assertTrue(ok, "%s verify_cmd 守卫拒: %s (%s)"
                                % (s["id"], why, s["verify_cmd"]))

    def test_seed_not_registered_in_index(self):
        with open(INDEX, encoding="utf-8") as f:
            body = f.read()
        self.assertNotIn("range-bizflow-v1", body,
                         "种子未激活不入注册表(注册=gt_verify 实跑,GT 未植必假失败)")

    def test_provenance_honest_seed_status(self):
        for c in self.doc["chains"]:
            self.assertIn("种子", c["provenance"],
                          "种子态出处如实(不冒充在案全过)")


if __name__ == "__main__":
    unittest.main()
