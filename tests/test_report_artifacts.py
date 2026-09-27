# -*- coding: utf-8 -*-
"""批次6 T15：双工件 findings.json+SARIF+LLM 叙述过滤+合规六要素签发面（契约 13 兑现）。

夹具=G-g1 复制+CLI 铸造（T14 test_report_lint.Base 同款 mint：add-evidence→卡片覆写
verified raw_request→add-finding exploitation-status=verified→add-goal 豁免行）。
时间戳全字面量（零墙钟纪律）；双工件=json 合法面+verified 纳入门+确定性逐字节。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import report_artifacts  # noqa: E402  T15 红点：模块缺=ImportError 全红
from tests.test_report_lint import repair_auth  # noqa: E402  批次 7 T8 夹具修补单源

FIX = os.path.join(HERE, "fixtures", "G-g1")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")
TS = "2026-09-24T09:00:00Z"
EV_ID, FD_ID = "EV-g1-0002", "FD-g1-0002"
RAW_REQUEST = "GET /admin/orders HTTP/1.1\nHost: admin-internal.shop.example\nAccept: */*"
CARD_TEXT = ("---\nid: %s\ntitle: admin 面板匿名可读-实验组\nsource_type: capture\n"
             % EV_ID
             + "observed_at: 2026-09-23T02:30:00Z\nnetwork_position: intranet\n"
             + "preconditions:\n  - 可解析 admin-internal.shop.example（DNS 内网视角）\n"
             + "raw_request: |\n  GET /admin/orders HTTP/1.1\n"
             + "  Host: admin-internal.shop.example\n  Accept: */*\n"
             + "expected: {}\ncleanup: ''\npair_group: \nrole: \n---\n"
             + "## 原始响应摘录（脱敏+定长）与判定依据\n"
             + "HTTP/1.1 200 OK（脱敏样例：未登录可读订单列表，token 化后原文）\n")


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mint(self):
        """CLI 铸 verified finding+EV 卡（T14 同款；豁免行=cleanup 核销判定前置）；
        批次 7 T8 起随铸授权三件套修补（签发授权门接线，补夹具不放水）。"""
        gd = self.gd
        repair_auth(gd)
        art = os.path.join(gd, "evidence", EV_ID + ".raw")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(RAW_REQUEST)
        r = run(os.path.join(ROOT, "cli", "tanyin-ledger"), "add-evidence", "--goal-dir", gd,
                "--title=admin 面板匿名可读-实验组", "--source-type=capture",
                "--observed-at=2026-09-23T02:30:00Z", "--network-position=intranet",
                "--repro-command=curl -s http://admin-internal.shop.example/admin/orders",
                "--repro-kind=single", "--artifact=evidence/" + EV_ID + ".raw",
                "--raw-excerpt=HTTP/1.1 200 OK 订单列表脱敏样例（token 化后）",
                "--timestamp=2026-09-23T02:35:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(gd, "evidence", EV_ID + ".md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(CARD_TEXT)
        r = run(os.path.join(ROOT, "cli", "tanyin-ledger"), "add-finding", "--goal-dir", gd,
                "--intent-id=INT-g1-0002", "--title=admin 面板匿名可读（双工件夹具）",
                "--confidence=C1", "--impact=高", "--exploitation-status=verified",
                "--scope-check=in_scope", "--description-brief=未登录可读订单列表（双工件夹具）",
                "--reproducible-steps=匿名 GET /admin/orders;响应 200 含订单列表",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=" + EV_ID,
                "--timestamp=2026-09-23T03:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(os.path.join(ROOT, "cli", "tanyin-ledger"), "approve", "--goal-dir", gd,
                "--command-hash=" + "b" * 64, "--decision=exempted", "--approver=客户",
                "--note=授权登记不可逆豁免 add-goal G-g1-0001",
                "--timestamp=2026-09-23T04:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def _unverified_ids(self, gd):
        """报告纳入门负集：active 且 exploitation_status!=verified 的 finding id 集。"""
        from ledger.schemas import TABLES
        from ledger.core import Session
        s = Session(gd)
        latest = {}
        for r in s.rows("findings.tsv"):
            latest[r[0]] = r
        si, xi = (TABLES["findings.tsv"].index("status"),
                  TABLES["findings.tsv"].index("exploitation_status"))
        return {fid for fid, r in latest.items()
                if r[si] == "active" and r[xi] != "verified"}


class TestFindingsJson(Base):
    def test_full_lifecycle(self):
        self._mint()
        d = report_artifacts.findings_json(self.gd)
        self.assertTrue(len(d["findings"]) >= 1)
        self.assertIn("replay_state", set(d["findings"][0].keys()))
        self.assertIn("lifecycle", set(d["findings"][0].keys()))

    def test_lifecycle_buckets_zero_new_facts(self):
        """全量=ledger findings id 集（无中生有=红）；桶值∈三枚举。"""
        self._mint()
        from ledger.core import Session
        s = Session(self.gd)
        ledger_ids = {r[0] for r in s.rows("findings.tsv")}
        d = report_artifacts.findings_json(self.gd)
        self.assertEqual({f["id"] for f in d["findings"]}, ledger_ids)
        for f in d["findings"]:
            self.assertIn(f["lifecycle"], ("active", "rejected", "repair-candidate"))

    def test_superseded_maps_rejected(self):
        """tombstone 行 lifecycle=rejected（supersede-finding 后）。

        同键 dup 行 craft=tests/test_write_cmds.TestSupersedeFinding/golden
        @craft-supersede 同款——add-finding 对 active 同键 REJECT，dup 只能夹具铸。"""
        self._mint()
        sys.path.insert(0, os.path.join(ROOT, "cli"))
        from ledger.core import esc, unesc
        from ledger.schemas import TABLES
        p = os.path.join(self.gd, "findings.tsv")
        with open(p, encoding="utf-8") as f:
            rows = [[unesc(c) for c in ln.split("\t")]
                    for ln in f.read().splitlines() if ln.strip()]
        fi = TABLES["findings.tsv"].index
        src = next(r for r in rows if r[0] == FD_ID)
        dup = list(src)
        dup[0] = "FD-g1-0003"
        rows.append(dup)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join("\t".join(esc(c) for c in r) for r in rows) + "\n")
        led = os.path.join(ROOT, "cli", "tanyin-ledger")
        r = run(led, "supersede-finding", "--goal-dir", self.gd,
                "--id=" + FD_ID, "--superseded-by=FD-g1-0003",
                "--timestamp=2026-09-23T03:50:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = report_artifacts.findings_json(self.gd)
        life = {f["id"]: f["lifecycle"] for f in d["findings"]}
        self.assertEqual(life[FD_ID], "rejected")
        self.assertEqual(life["FD-g1-0003"], "active")   # dst 行仍在活集

    def test_deterministic_bytes(self):
        self._mint()
        a = json.dumps(report_artifacts.findings_json(self.gd), ensure_ascii=False,
                       sort_keys=True)
        b = json.dumps(report_artifacts.findings_json(self.gd), ensure_ascii=False,
                       sort_keys=True)
        self.assertEqual(a, b, "零墙钟确定性：同输入两跑逐字节一致")


class TestSarif(Base):
    def test_verified_only(self):
        self._mint()
        d = report_artifacts.findings_sarif(self.gd)
        results = d["runs"][0]["results"]
        self.assertTrue(results, "verified finding 在册时 SARIF 非空")
        fids = {r["properties"]["finding_id"] for r in results}
        self.assertEqual(fids & self._unverified_ids(self.gd), set())  # 报告纳入门
        from ledger.schemas import TABLES
        from ledger.core import Session
        s = Session(self.gd)
        latest = {}
        for r in s.rows("findings.tsv"):
            latest[r[0]] = r
        si = TABLES["findings.tsv"].index("status")
        active = {fid for fid, r in latest.items() if r[si] == "active"}
        self.assertTrue(fids <= active, "SARIF 仅收 active 面")

    def test_sarif_shape(self):
        self._mint()
        d = report_artifacts.findings_sarif(self.gd)
        self.assertEqual(d["version"], "2.1.0")
        self.assertTrue(all("artifactLocation" in r["locations"][0]["physicalLocation"]
                            for r in d["runs"][0]["results"]))
        self.assertTrue(all(r["level"] in ("error", "warning", "note")
                            for r in d["runs"][0]["results"]))
        # EV↔SARIF 位置映射：artifactLocation=EV 卡片相对路径（卡片在盘）
        for r in d["runs"][0]["results"]:
            uri = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            self.assertFalse(os.path.isabs(uri), uri)
            self.assertTrue(os.path.isfile(os.path.join(self.gd, uri)), uri)

    def test_rule_id_is_vuln_class(self):
        """ruleId=漏洞类型（矩阵词表锚）；夹具 verified finding 锚=authz.diff。"""
        self._mint()
        d = report_artifacts.findings_sarif(self.gd)
        rules = {r["ruleId"] for r in d["runs"][0]["results"]}
        self.assertIn("authz.diff", rules)
        driver = d["runs"][0]["tool"]["driver"]
        self.assertTrue(any(x["id"] == "authz.diff" for x in driver["rules"]))


class TestFilter(unittest.TestCase):
    def test_strips_markers(self):
        dirty = "<think>推理</think>TOOL_CALL add-finding\nRound 3\n结论：存在 SQLi。"
        clean = report_artifacts.narrative_filter(dirty)
        self.assertNotIn("TOOL_CALL", clean)
        self.assertNotIn("<think>", clean)
        self.assertIn("结论：存在 SQLi。", clean)

    def test_multiline_think_and_round(self):
        dirty = "<think>\n多行推理\n保留不住\n</think>\n── Round 7 ──\n正文保留段"
        clean = report_artifacts.narrative_filter(dirty)
        self.assertNotIn("多行推理", clean)
        self.assertNotIn("Round 7", clean)
        self.assertIn("正文保留段", clean)

    def test_sep_line_narrow_keeps_wrapped_label(self):
        """M-1 评审收尾：_SEP_LINE 收窄为纯标线——『──事实──』包裹行保留（反例测试）。"""
        dirty = "──事实──\n正文行保留\n────────────────\n结论行"
        clean = report_artifacts.narrative_filter(dirty)
        self.assertIn("──事实──", clean)
        self.assertIn("正文行保留", clean)
        self.assertNotIn("────────────────", clean, "纯标线仍剥（收窄不放松）")

    def test_debug_prefix_lines(self):
        dirty = "[LLM THINKING] 内部态\n[结果] ok\n结论正文行"
        clean = report_artifacts.narrative_filter(dirty)
        self.assertNotIn("[LLM THINKING]", clean)
        self.assertIn("结论正文行", clean)


class TestWriteAll(Base):
    def test_three_artifacts(self):
        self._mint()
        paths = report_artifacts.write_all(self.gd, TS)
        for suffix in ("findings.json", "findings.sarif"):
            self.assertTrue(any(p.endswith(suffix) for p in paths))
        self.assertTrue(all(os.path.isfile(p) for p in paths))
        # 终稿 md 含合规六要素六标题（等保占位段原文在；契约 13 §1）
        md = open([p for p in paths if p.endswith(".md")][0], encoding="utf-8").read()
        for h in ("授权与范围声明", "方法学映射", "覆盖度与局限性", "技术×业务风险分级",
                  "整改优先级与复测建议", "等保"):
            self.assertIn(h, md)
        json.load(open([p for p in paths if p.endswith("findings.json")][0], encoding="utf-8"))
        sar = json.load(open([p for p in paths if p.endswith("findings.sarif")][0],
                             encoding="utf-8"))
        self.assertEqual(sar["version"], "2.1.0")

    def test_final_md_contains_fd_render_and_filtered_summary(self):
        """终稿=聚合投影+FD 九段渲染+执行摘要（narrative_filter 后无 TOOL_CALL）。"""
        self._mint()
        paths = report_artifacts.write_all(self.gd, TS)
        md = open([p for p in paths if p.endswith(".md")][0], encoding="utf-8").read()
        self.assertIn(FD_ID, md)                       # FD 九段渲染并入
        self.assertIn("执行摘要", md)
        self.assertNotIn("TOOL_CALL", md)

    def test_sign_cli_wires_write_all(self):
        """T14 预留接线点激活：sign rc=0 落三工件+不再披露「双工件未接线」。"""
        self._mint()
        r = run(REPORT, "sign", "--goal-dir", self.gd, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.gd, "report", "signed", "pass.json")))
        self.assertNotIn("未接线", r.stdout, "中间态披露行已删（T15 接线完成）")
        self.assertTrue(os.path.exists(os.path.join(self.gd, "report", "findings.json")))
        self.assertTrue(os.path.exists(os.path.join(self.gd, "report", "findings.sarif")))
        signed = os.listdir(os.path.join(self.gd, "report", "signed"))
        self.assertTrue(any(fn.startswith("report-") and fn.endswith(".md") for fn in signed),
                        signed)


if __name__ == "__main__":
    unittest.main()
