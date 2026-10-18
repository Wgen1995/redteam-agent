# -*- coding: utf-8 -*-
"""功能24a·外部执行后端④：归一入账（TDD 红先行）——本舰的心脏。

设计定稿 §3 记录行归一律：外部肌肉产的事实/发现走我们全部质量门
（哨兵前置→验证官复放→GT 棘轮），**零豁免**——与 Multica 的根本差异
（它无质量门层）。归一通道=registry.lookup("add-evidence"/"add-finding"/
"add-fact"/"budget-log")：goal 写锁+既有校验执法链原样生效，绝不私铸
TSV 行（规划者舰 R-PLN-3 同款纪律）。

咬住的契约：
- 外部 result.output=输出契约 JSON（facts/findings+evidence）→ 逐条经
  既有命令入账；证据先铸（findings 须 evidence_ids 闭合=铁律 4）。
- **哨兵零豁免**：外部产的 finding 命中哨兵（SEN-001 类）同样被降级
  成 fact——测试必须证明，不是嘴说说。
- 枚举校验前置：confidence/impact/exploitation_status/scope_check 不合
  账本枚举=拒收（记 rejected，不硬编不猜）。
- 结果不可归一 → 记原始流（backends/<task>.raw.jsonl）+ timeline
  backend-unnormalizable 事件=人工通道，不硬编（设计 §失败怎么办）。
- usage 四 token 维 → budget-log 入 budget.tsv（dollars 维只在 goal
  开了 dollar_budget 才入账——ADR-P4⑥ 既有执法）。

跑法：python3 -m unittest tests.test_backends_ingest -v
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

from ledger import registry  # noqa: E402
from ledger.core import Session  # noqa: E402
from ledger.timeline import read_rows  # noqa: E402
from backends import base, ingest  # noqa: E402

TS = "2026-10-20T10:00:00Z"


def _result(payload):
    return base.Result(status="ok", output=json.dumps(payload,
                                                      ensure_ascii=False))


GOOD_FINDING = {
    "title": "admin 面板未授权访问",
    "confidence": "C2",
    "impact": "高",
    "exploitation_status": "verified",
    "scope_check": "in_scope",
    "description_brief": "未认证访问 admin 面板可见订单数据",
    "reproducible_steps": "GET /admin/orders 返回 200 与订单列表",
    "affected_asset_id": "AST-g1-0002",
    "vuln_ref": "CWE-200",
    "evidence": {"excerpt": "HTTP/1.1 200 OK orders list",
                 "repro": "curl -s https://admin-internal.shop.example/admin/orders"},
}
GOOD_FACT = {"kind": "http", "target": "admin-internal.shop.example",
             "detail": "admin 面板 200 可达", "confidence": "0.8"}

class IngestCase(unittest.TestCase):
    def setUp(self):
        self.gd = shutil.copytree(FIX, tempfile.mkdtemp() + "/G-ig")
        self.addCleanup(shutil.rmtree, self.gd, ignore_errors=True)

    def _ingest(self, result, backend="dsh", task_id="T-ig-1",
                intent_id="INT-g1-0002", frames=None):
        return ingest.ingest_result(
            self.gd, backend_name=backend, task_id=task_id, result=result,
            frames=frames if frames is not None else [], ts=TS,
            intent_id=intent_id)

    def _rows(self, table):
        return Session(self.gd).rows(table)

    def _events(self):
        return [r[3] for r in read_rows(self.gd)]

    # --- ① 正常归一：证据先行，finding/fact 落账 -------------------------

    def test_valid_finding_and_fact_ingested_via_ledger_chain(self):
        rep = self._ingest(_result({"findings": [GOOD_FINDING],
                                    "facts": [GOOD_FACT]}))
        self.assertEqual(rep["normalizable"], True)
        evs = [r for r in self._rows("E-index.tsv")
               if r[0].startswith("EV-") and "T-ig-1" in (r[9] or "")]
        self.assertEqual(len(evs), 1)
        fd = [r for r in self._rows("findings.tsv") if r[1] == "INT-g1-0002"
              and r[2] == "admin 面板未授权访问"]
        self.assertEqual(len(fd), 1)
        self.assertIn(fd[0][0], rep["findings"])
        self.assertEqual(fd[0][8], "CWE-200")
        self.assertEqual(fd[0][5], "verified")
        facts = [r for r in self._rows("facts.tsv") if r[4] == "admin 面板 200 可达"]
        self.assertEqual(len(facts), 1)
        # 全部经既有命令链：timeline 有三类事件行
        for ev in ("add-evidence", "add-finding", "add-fact"):
            self.assertTrue(any(e.startswith(ev) for e in self._events()), ev)

    def test_evidence_artifact_lands_in_backend_dir(self):
        rep = self._ingest(_result({"findings": [GOOD_FINDING]}))
        art = [r for r in self._rows("E-index.tsv")
               if r[0] not in ("EV-g1-0001",)][0][9]
        self.assertTrue(art.startswith("backends/T-ig-1/"))
        self.assertTrue(os.path.isfile(os.path.join(self.gd, art)))

    # --- ② 哨兵零豁免（心脏测试） ---------------------------------------

    def test_external_finding_downgraded_by_sentinel_zero_exemption(self):
        """外部产 finding 命中 SEN-001 → 哨兵照样降级为 fact 入账。"""
        bad = dict(GOOD_FINDING)
        bad["title"] = "admin 面板 404 页面暴露未授权访问"
        bad["description_brief"] = "404 响应页面可访问敏感接口"
        rep = self._ingest(_result({"findings": [bad]}))
        # findings 零行新增——外部身份不是豁免理由
        self.assertEqual(
            [r for r in self._rows("findings.tsv")
             if r[2] == bad["title"]], [])
        self.assertEqual(len(rep["downgraded"]), 1)
        dg = [r for r in self._rows("facts.tsv")
              if "SEN-001" in r[4] and "哨兵降级" in r[4]]
        self.assertEqual(len(dg), 1)             # 降级 fact 真落账
        self.assertEqual(dg[0][1], "INT-g1-0002")

    def test_external_finding_rejected_by_sentinel(self):
        """SEN-011 类 reject 规则：外部 finding 直接拒收（不入任何表）。"""
        bad = dict(GOOD_FINDING)
        bad["title"] = "代理低置信疑似可能有效的凭据已实测确认"
        before_f = len(self._rows("findings.tsv"))
        before_c = len(self._rows("facts.tsv"))
        rep = self._ingest(_result({"findings": [bad]}))
        self.assertEqual(len(rep["rejected"]), 1)
        self.assertIn("哨兵拒收", rep["rejected"][0]["why"])
        self.assertEqual(len(self._rows("findings.tsv")), before_f)
        self.assertEqual(len(self._rows("facts.tsv")), before_c)

    # --- ③ 枚举校验前置 ---------------------------------------------------

    def test_invalid_confidence_enum_rejected_before_write(self):
        bad = dict(GOOD_FINDING)
        bad["confidence"] = "C9"
        rep = self._ingest(_result({"findings": [bad]}))
        self.assertEqual(len(rep["rejected"]), 1)
        self.assertIn("confidence", rep["rejected"][0]["why"])
        self.assertEqual([r for r in self._rows("findings.tsv")
                          if r[2] == bad["title"]], [])

    def test_missing_required_finding_field_rejected(self):
        bad = dict(GOOD_FINDING)
        del bad["reproducible_steps"]
        rep = self._ingest(_result({"findings": [bad]}))
        self.assertEqual(len(rep["rejected"]), 1)

    def test_invalid_fact_kind_rejected(self):
        rep = self._ingest(_result({"facts": [dict(GOOD_FACT, kind="zzz")]}))
        self.assertEqual(len(rep["rejected"]), 1)
        self.assertEqual([r for r in self._rows("facts.tsv")
                          if r[2] == "zzz"], [])

    def test_broken_asset_reference_rejected_by_ledger_chain(self):
        """affected_asset_id 闭合失败——既有执法链拒（我们不开旁门）。"""
        bad = dict(GOOD_FINDING)
        bad["affected_asset_id"] = "AST-nope-9999"
        rep = self._ingest(_result({"findings": [bad]}))
        self.assertEqual(len(rep["rejected"]), 1)
        self.assertIn("引用闭合失败", rep["rejected"][0]["why"])

    # --- ④ 不可归一 → 原始流+人工通道 -------------------------------------

    def test_unnormalizable_output_goes_raw_channel(self):
        rep = self._ingest(base.Result(status="ok", output="我不会是 JSON 的"),
                           task_id="T-raw-9",
                           frames=[{"v": 1, "type": "text", "text": "碎片"}])
        self.assertEqual(rep["normalizable"], False)
        raw = os.path.join(self.gd, "backends", "T-raw-9.raw.jsonl")
        self.assertTrue(os.path.isfile(raw))
        with open(raw, encoding="utf-8") as f:
            dumped = f.read()
        self.assertIn("碎片", dumped)
        self.assertIn("我不会是 JSON 的", dumped)
        # 人工通道=timeline 事件行（可回放可验真）
        self.assertTrue(any("backend-unnormalizable" in e and "T-raw-9" in e
                            for e in self._events()))
        self.assertEqual(rep["findings"], [])

    def test_fenced_json_output_accepted(self):
        payload = {"facts": [GOOD_FACT]}
        fenced = "```json\n%s\n```" % json.dumps(payload, ensure_ascii=False)
        rep = self._ingest(base.Result(status="ok", output=fenced))
        self.assertEqual(rep["normalizable"], True)
        self.assertEqual(len(rep["facts"]), 1)

    # --- ⑤ usage → budget.tsv -------------------------------------------

    def test_usage_logged_to_budget(self):
        u = base.Usage(input_tokens=100, output_tokens=40,
                       cache_read_tokens=7, cache_write_tokens=3)
        rep = self._ingest(base.Result(status="ok", output="{}", usage=u))
        self.assertTrue(rep["budget_logged"])
        rows = [r for r in self._rows("budget.tsv")
                if r[5] == "INT-g1-0002" and "backend=dsh" in r[6]]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "150")      # 四维全计
        self.assertEqual(rows[0][2], "1")
        self.assertEqual(rows[0][4], "0")        # goal dollar_budget 关=0

    def test_dollars_logged_only_when_goal_enables(self):
        gp = os.path.join(self.gd, "goals.tsv")
        with open(gp, encoding="utf-8") as f:
            lines = f.read().splitlines()
        cols = lines[-1].split("\t")
        cols[12] = "100"                          # dollar_budget 开
        lines[-1] = "\t".join(cols)
        with open(gp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        u = base.Usage(cost_usd_ticks=7)
        rep = self._ingest(base.Result(status="ok", output="{}", usage=u))
        rows = [r for r in self._rows("budget.tsv") if "backend=dsh" in r[6]]
        self.assertEqual(rows[0][4], "0.0000000007")

    def test_failed_result_not_ingested_but_usage_still_billed(self):
        """后端崩了：产出不归一（error 无 output），钱照记（真实消耗）。"""
        rep = self._ingest(base.Result(status="error",
                                       error={"code": "backend-died",
                                              "message": "x"},
                                       usage=base.Usage(input_tokens=5)))
        self.assertEqual(rep["normalizable"], False)
        self.assertTrue(rep["budget_logged"])

    # --- ⑥ 链完整性：零豁免=全部过锁与验证官 ------------------------------

    def test_chain_validate_still_passes_after_ingest(self):
        self._ingest(_result({"findings": [GOOD_FINDING],
                              "facts": [GOOD_FACT]}))
        rc = registry.lookup("validate")(self.gd, [])
        self.assertEqual(rc, 0)                   # 既有验证官全绿


if __name__ == "__main__":
    unittest.main()
