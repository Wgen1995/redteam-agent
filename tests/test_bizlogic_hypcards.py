# -*- coding: utf-8 -*-
"""功能6 TDD③: 作弊假设卡模板(cli/bizlogic/hypcards.py)——先失败测试。

设计: docs/design/2026-10-20-bizlogic-layer-design.md §3(判据先行)/§5(可逆纪律)。
纪律:
- 判据先行(吸收 GenSift): 每条假设必带 truth_criteria(判真标准)——无判据不立卡;
- 可逆纪律: reversibility∈{rollback-able,test-account,irreversible};
  irreversible→approval_required(挂审批等人放行);rollback-able→必带 rollback_cmd;
- 不自建调度: 卡只铸造/校验;入池走既有 ledger-add-intent 命令面(kind=engine-hyp),
  池兼容性如实探测(write_cmds._INTENT_KINDS 现况)——未入枚举=诚实报 pending-enum。
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

from bizlogic import hypcards  # noqa: E402


class TestMakeCard(unittest.TestCase):
    def _base(self, **kw):
        args = {"hypothesis": "下单金额参数可被客户端改写(改价)",
                "truth_criteria": ["改价后订单成交金额=改写值(查订单详情接口对账)",
                                   "未改价对照单金额=原价"],
                "reversibility": "test-account",
                "title": "shop/orders 改价假设",
                "target": "shop.example/orders",
                "biz_step": "下单",
                "test_account_cred": "CRED-bizlogic-keys-0004"}
        args.update(kw)
        return args

    def test_card_shape(self):
        card = hypcards.make_card(**self._base())
        self.assertEqual(card["kind"], "engine-hyp")
        self.assertEqual(card["origin"], "llm", "LLM 业务流还原产物 origin=llm")
        self.assertTrue(card["truth_criteria"])
        self.assertFalse(card["approval_required"])

    def test_truth_criteria_mandatory(self):
        with self.assertRaises(hypcards.CardReject) as cm:
            hypcards.make_card(**self._base(truth_criteria=[]))
        self.assertIn("判真标准", str(cm.exception), "判据先行: 无判据不立卡")

    def test_reversibility_enum(self):
        with self.assertRaises(hypcards.CardReject):
            hypcards.make_card(**self._base(reversibility="yolo"))

    def test_irreversible_requires_approval(self):
        card = hypcards.make_card(**self._base(reversibility="irreversible",
                                               test_account_cred=""))
        self.assertTrue(card["approval_required"],
                        "不可逆且无测试账号=挂审批等人放行(设计§5红线)")

    def test_rollbackable_requires_rollback_cmd(self):
        with self.assertRaises(hypcards.CardReject):
            hypcards.make_card(**self._base(reversibility="rollback-able"))
        card = hypcards.make_card(**self._base(reversibility="rollback-able",
                                               test_account_cred="",
                                               rollback_cmd="ledger 侧删除测试单 FD-x"))
        self.assertFalse(card["approval_required"])

    def test_validate_roundtrip(self):
        card = hypcards.make_card(**self._base())
        self.assertEqual(hypcards.validate_card(card), [])
        broken = dict(card)
        broken["truth_criteria"] = []
        self.assertTrue(hypcards.validate_card(broken), "校验面捕捉残卡")


class TestIntentArgs(unittest.TestCase):
    def test_to_add_intent_args(self):
        card = hypcards.make_card(
            hypothesis="优惠券单次券可重用",
            truth_criteria=["同券码二次抵扣响应=成功且订单再减同额"],
            reversibility="test-account",
            title="shop/coupon 重用假设", target="shop.example/coupon",
            biz_step="支付", test_account_cred="CRED-bizlogic-keys-0004")
        args = hypcards.to_add_intent_args(card)
        self.assertEqual(args["kind"], "engine-hyp")
        self.assertEqual(args["origin"], "llm")
        self.assertIn("budget-share", args, "add-intent 必填面齐(budget-share)")
        detail = json.loads(args["detail"])
        self.assertEqual(detail["truth_criteria"][0].startswith("同券码"), True,
                         "结构化判据随 detail 入池(detail=json 承载,零 schema 改动)")
        self.assertEqual(args["cred"], "CRED-bizlogic-keys-0004")
        self.assertTrue(args.get("dedup_key_proposed"), "LLM 只提议不判重(契约01)")

    def test_irreversible_card_marks_approval(self):
        card = hypcards.make_card(
            hypothesis="取消后订单仍可触发发货",
            truth_criteria=["取消态下单触发发货→订单状态变已发货"],
            reversibility="irreversible",
            title="shop/ship 取消后发货假设", target="shop.example/ship",
            biz_step="发货", test_account_cred="")
        args = hypcards.to_add_intent_args(card)
        detail = json.loads(args["detail"])
        self.assertTrue(detail["approval_required"])
        self.assertTrue(hypcards.needs_approval(card))


class TestPoolStatus(unittest.TestCase):
    def test_pool_status_honest_probe(self):
        ok, detail = hypcards.pool_status()
        self.assertIsInstance(ok, bool)
        self.assertTrue(detail, "探测结果带人话说明")
        if not ok:
            self.assertIn("pending-enum", detail,
                          "枚举未开=诚实报 pending-enum,不绕过不私扩")

    def test_pool_status_branches(self):
        ok, _ = hypcards.pool_status(kinds={"recon", "engine-hyp"})
        self.assertTrue(ok, "枚举已含 engine-hyp → 可入池")
        ok, detail = hypcards.pool_status(kinds={"recon"})
        self.assertFalse(ok)
        self.assertIn("pending-enum", detail)

    def test_matches_write_cmds_reality(self):
        """与 write_cmds 现况对表: 探测结论不漂(单源读,不复制枚举)。"""
        try:
            from ledger import write_cmds
        except ImportError:
            self.skipTest("write_cmds 不可导入")
        ok, _ = hypcards.pool_status()
        self.assertEqual(ok, "engine-hyp" in write_cmds._INTENT_KINDS)


if __name__ == "__main__":
    unittest.main()
