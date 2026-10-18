# -*- coding: utf-8 -*-
"""功能26 报告补件（TDD 红点面）：证据角色+证据集版本+过期拒写门+manifest 过期检测
+报告员兵种模板。

设计稿=docs/design/2026-10-20-report-upgrade-design.md 补件一/二/三：
- ①证据绑定带角色（proof/baseline/verification/supporting）与顺序；证据集版本号
  （绑定增删改=+1）；report_artifacts 渲染输出 evidence_version。
- ②过期拒写门：render 携带的 evidence_version 与账本当前不符=rc 1 FAIL
  （why=「证据已变化,待重写」）——进 report_lint sign_gate。
- ③报告员兵种模板：权限=只读账本+EV；卡文=只写不判/产物必须过 sign_gate/
  被打回≤2 轮转人工。
- ④manifest 过期检测：write_all 落 report-manifest（各 finding 的
  evidence_version 快照）；下次渲染前比对，漂移=输出待重写清单不渲染半新半旧。

mint=直铸 TSV 行（零 write_cmds 依赖——兄弟舰在改 write_cmds.py 时本文件仍可
独立跑绿；行形=CLI _row 同构、值=29 测夹具同源，repair_auth 复用单源）。
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
from ledger import report_evidence  # noqa: E402  功能26 红点：模块缺=ImportError 全红
from tests.test_report_lint import (  # noqa: E402  夹具常量+授权修补单源
    CARD_TEXT, EV_ID, FD_ID, FIX, RAW_REQUEST, TS, repair_auth)

REPORT = os.path.join(ROOT, "cli", "tanyin-report")
ROLE_CARD = os.path.join(ROOT, ".opencode", "skills", "pentest-report", "SKILL.md")


class MintBase(unittest.TestCase):
    """G-g1 复制+直铸（EV 工件/E-index 行/EV 卡/findings 行/豁免 approvals 行）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _append_row(self, tname, **kw):
        from ledger.core import esc
        from ledger.schemas import TABLES
        cols = TABLES[tname]
        r = [""] * len(cols)
        for k, v in kw.items():
            r[cols.index(k)] = "" if v is None else str(v)
        if "schema_version" in cols:
            r[cols.index("schema_version")] = "2"
        with open(os.path.join(self.gd, tname), "a", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(esc(c) for c in r) + "\n")

    def _mint(self):
        gd = self.gd
        repair_auth(gd)
        art = os.path.join(gd, "evidence", EV_ID + ".raw")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(RAW_REQUEST)
        from ledger.norm import artifact_hashes
        with open(art, "rb") as f:
            raw_h, norm_h = artifact_hashes(f.read())
        self._append_row(
            "E-index.tsv", id=EV_ID, title="admin 面板匿名可读-实验组",
            source_type="capture", observed_at="2026-09-23T02:30:00Z",
            network_position="intranet",
            repro_command="curl -s http://admin-internal.shop.example/admin/orders",
            repro_kind="single", content_hash_raw=raw_h, content_hash_norm=norm_h,
            artifact_path="evidence/" + EV_ID + ".raw",
            card_path="evidence/" + EV_ID + ".md", linked_finding="",
            pair_group="", raw_excerpt="HTTP/1.1 200 OK 订单列表脱敏样例（token 化后）",
            created="2026-09-23T02:35:00Z")
        with open(os.path.join(gd, "evidence", EV_ID + ".md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(CARD_TEXT)
        title = "admin 面板匿名可读（证据版本夹具）"
        self._append_row(
            "findings.tsv", id=FD_ID, intent_id="INT-g1-0002", title=title,
            confidence="C1", impact="高", exploitation_status="verified",
            dedup_key="AST-g1-0002+" + title, scope_check="in_scope",
            description_brief="未登录可读订单列表（证据版本夹具）",
            reproducible_steps="匿名 GET /admin/orders;响应 200 含订单列表",
            affected_asset_id="AST-g1-0002", evidence_ids=EV_ID,
            card_path="findings-cards/%s.md" % FD_ID, status="active",
            created="2026-09-23T03:30:00Z")
        self._append_row(
            "approvals.tsv", id="AP-g1-0002", command_hash="b" * 64,
            decision="exempted", approver="客户", timestamp="2026-09-23T04:00:00Z",
            note="授权登记不可逆豁免 add-goal G-g1-0001")


class TestEvidenceRoleVersion(MintBase):
    def test_base_bindings_and_version_one(self):
        """①基线：evidence_ids→proof、control→baseline；初始版本=1。"""
        self._mint()
        bs = report_evidence.bindings(self.gd, FD_ID)
        self.assertEqual([b["evidence_id"] for b in bs], [EV_ID])
        self.assertEqual(bs[0]["role"], "proof")
        self.assertEqual(bs[0]["order"], 1)
        self.assertEqual(report_evidence.evidence_version(self.gd, FD_ID), 1)

    def test_bind_rebind_unbind_each_bumps_one(self):
        """②绑定增删改=版本+1（bind/rebind/unbind 各+1，角色与顺序随记随生效）。"""
        self._mint()
        v = report_evidence.append_binding(self.gd, FD_ID, EV_ID, "supporting",
                                           timestamp="2026-09-24T01:00:00Z")
        self.assertEqual(v, 2)
        self.assertEqual(report_evidence.evidence_version(self.gd, FD_ID), 2)
        self.assertEqual(report_evidence.bindings(self.gd, FD_ID)[0]["role"],
                         "supporting")
        v = report_evidence.append_binding(self.gd, FD_ID, EV_ID, "verification",
                                           order=2, timestamp="2026-09-24T01:05:00Z")
        self.assertEqual(v, 3)
        b = report_evidence.bindings(self.gd, FD_ID)[0]
        self.assertEqual((b["role"], b["order"]), ("verification", 2))
        v = report_evidence.append_binding(self.gd, FD_ID, EV_ID, action="unbind",
                                           timestamp="2026-09-24T01:10:00Z")
        self.assertEqual(v, 4)
        self.assertEqual(report_evidence.bindings(self.gd, FD_ID), [])

    def test_unknown_role_rejected_no_bump(self):
        """角色词表外/引用不闭合=fail-closed 拒写，版本不动。"""
        self._mint()
        with self.assertRaises(ValueError):
            report_evidence.append_binding(self.gd, FD_ID, EV_ID, "root-cause",
                                           timestamp="2026-09-24T01:00:00Z")
        self.assertEqual(report_evidence.evidence_version(self.gd, FD_ID), 1)
        with self.assertRaises(ValueError):
            report_evidence.append_binding(self.gd, FD_ID, "EV-nope", "proof",
                                           timestamp="2026-09-24T01:00:00Z")

    def test_control_evidence_role_baseline_and_bump(self):
        """findings 修订行改 control_evidence_ids=绑定变化：baseline 角色+版本+1。"""
        self._mint()
        self._append_row("findings.tsv", id=FD_ID, intent_id="INT-g1-0002",
                         title="admin 面板匿名可读（证据版本夹具）", confidence="C1",
                         impact="高", exploitation_status="verified",
                         dedup_key="AST-g1-0002+admin 面板匿名可读（证据版本夹具）",
                         scope_check="in_scope",
                         description_brief="未登录可读订单列表（证据版本夹具）",
                         reproducible_steps="匿名 GET /admin/orders;响应 200 含订单列表",
                         affected_asset_id="AST-g1-0002", evidence_ids=EV_ID,
                         control_evidence_ids="EV-g1-0001",
                         card_path="findings-cards/%s.md" % FD_ID, status="active",
                         created="2026-09-23T03:40:00Z")
        bs = report_evidence.bindings(self.gd, FD_ID)
        roles = {b["evidence_id"]: b["role"] for b in bs}
        self.assertEqual(roles[EV_ID], "proof")
        self.assertEqual(roles["EV-g1-0001"], "baseline")
        self.assertEqual(report_evidence.evidence_version(self.gd, FD_ID), 2)

    def test_findings_json_carries_version_and_roles(self):
        """①report_artifacts 渲染输出 evidence_version+带角色证据清单。"""
        self._mint()
        from ledger import report_artifacts
        d = report_artifacts.findings_json(self.gd)
        f = next(x for x in d["findings"] if x["id"] == FD_ID)
        self.assertEqual(f["evidence_version"], 1)
        self.assertIn({"evidence_id": EV_ID, "role": "proof", "order": 1},
                      f["evidence"])


class TestStaleGate(MintBase):
    def test_render_fd_stale_carried_version_rejected(self):
        """②render 携带 evidence_version 与账本不符=rc 1 FAIL（why=证据已变化,待重写）。"""
        self._mint()
        from ledger import report_render
        rc, md = report_render.render_fd(self.gd, FD_ID, evidence_version=2)
        self.assertEqual(rc, 1)
        self.assertIn("证据已变化,待重写", md)
        rc, md = report_render.render_fd(self.gd, FD_ID, evidence_version=1)
        self.assertEqual(rc, 0, md)
        rc, md = report_render.render_fd(self.gd, FD_ID)   # 不携带=既有口径不破
        self.assertEqual(rc, 0, md)

    def test_sign_gate_freshness_fail_after_drift(self):
        """②漂移进 sign_gate：evidence_freshness FAIL rc 1，明细载 stale finding。"""
        self._mint()
        from ledger import report_artifacts, report_lint
        report_artifacts.write_all(self.gd, TS)
        report_evidence.append_binding(self.gd, FD_ID, EV_ID, "verification",
                                       timestamp="2026-09-24T10:00:00Z")
        rc, rep = report_lint.sign_gate(self.gd, TS, write_credential=False)
        self.assertEqual(rc, 1)
        g = rep["gates"]["evidence_freshness"]
        self.assertEqual(g["status"], "FAIL")
        self.assertIn("证据已变化,待重写", g["detail"])
        self.assertIn(FD_ID, g["detail"])

    def test_lint_cli_drift_rc1(self):
        """lint CLI 面：漂移=rc 1 且报文载待重写清单（不渲染半新半旧）。"""
        self._mint()
        from ledger import report_artifacts
        report_artifacts.write_all(self.gd, TS)
        report_evidence.append_binding(self.gd, FD_ID, EV_ID, "supporting",
                                       timestamp="2026-09-24T10:00:00Z")
        r = subprocess.run([sys.executable, REPORT, "lint", "--goal-dir", self.gd,
                            "--timestamp=" + TS], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("证据已变化,待重写", r.stdout)
        self.assertIn(FD_ID, r.stdout)


class TestManifestStale(MintBase):
    def test_write_all_writes_manifest_snapshot(self):
        """④write_all 落 report-manifest：active finding 的 evidence_version 快照。"""
        self._mint()
        from ledger import report_artifacts
        paths = report_artifacts.write_all(self.gd, TS)
        self.assertTrue(any(p.endswith("report-manifest.json") for p in paths), paths)
        p = os.path.join(self.gd, "report", "report-manifest.json")
        with open(p, encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(m["evidence_versions"].get(FD_ID), 1)
        self.assertEqual(m["ts"], TS)

    def test_write_all_refuses_drift_no_partial_write(self):
        """④漂移=拒写：StaleEvidenceError+findings.json 字节不动（不产半新半旧）。"""
        self._mint()
        from ledger import report_artifacts
        report_artifacts.write_all(self.gd, TS)
        fj = os.path.join(self.gd, "report", "findings.json")
        with open(fj, "rb") as f:
            before = f.read()
        report_evidence.append_binding(self.gd, FD_ID, EV_ID, "supporting",
                                       timestamp="2026-09-24T10:00:00Z")
        with self.assertRaises(report_evidence.StaleEvidenceError) as cm:
            report_artifacts.write_all(self.gd, TS)
        self.assertIn(FD_ID, cm.exception.stale_ids())
        with open(fj, "rb") as f:
            self.assertEqual(f.read(), before, "漂移后不得重写半新半旧工件")

    def test_rewrite_evidence_recovers_then_sign_passes(self):
        """④恢复路径：rewrite-evidence 重渲染+manifest 刷新后 sign 复绿（两轮帽内）。"""
        self._mint()
        from ledger import report_lint
        self.assertEqual(report_lint.cmd_sign(self.gd, TS), 0)
        report_evidence.append_binding(self.gd, FD_ID, EV_ID, "verification",
                                       timestamp="2026-09-24T10:00:00Z")
        self.assertEqual(report_lint.cmd_sign(self.gd, TS), 1)   # 漂移=拒签
        rc, detail = report_evidence.rewrite_evidence(self.gd, TS)
        self.assertEqual(rc, 0, str(detail))
        self.assertEqual(report_lint.cmd_sign(self.gd, TS), 0)   # 重写后复绿


class TestReporterCard(unittest.TestCase):
    def test_reporter_card_exists_and_pleads(self):
        """③报告员兵种模板：六维配置+卡文三纪律（只写不判/过 sign_gate/≤2 轮转人工）。"""
        self.assertTrue(os.path.isfile(ROLE_CARD), ROLE_CARD)
        with open(ROLE_CARD, encoding="utf-8") as f:
            txt = f.read()
        parts = txt.split("---")
        self.assertGreaterEqual(len(parts), 3, "YAML frontmatter 形（既有兵种卡同构）")
        head, body = parts[1], txt.split("---", 2)[2]
        for key in ("name:", "description:", "permissions:", "backend:"):
            self.assertIn(key, head)
        self.assertIn("只读", head)                # 权限=只读账本+EV
        self.assertIn("warrior", head)             # 执行后端=warrior
        self.assertIn("只写不判", body)             # 与验证官分工
        self.assertIn("sign_gate", body)           # 产物必须过签发门
        self.assertIn("≤2 轮", body)                # 两轮修复帽（cyber-audit 借鉴）
        self.assertIn("转人工", body)
        self.assertIn("evidence_version", body)    # 证据版本纪律（重读重写）


if __name__ == "__main__":
    unittest.main()
