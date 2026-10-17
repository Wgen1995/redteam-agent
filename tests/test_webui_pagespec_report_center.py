# -*- coding: utf-8 -*-
"""T4·P7 报告中心完整版——列表+详情+重渲染钉+签发流四态页钉测。

python3 -m unittest tests.test_webui_pagespec_report_center
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P7；文案宪法#41（战报→报告）。

四层钉：
  ①列表投影  api_v2_reports.report_list_view——每仗一行：状态徽章
             （草稿/待签发/已签发，确定性分类）+版本数+最后渲染时间；
  ②详情投影  report_detail_view——左侧渲染预览六节（封面/授权摘要/发现表
             [等级/验证状态徽章]/证据附录/覆盖诚实节=已测矩阵+未测清单+原因/
             方法论附录）+右侧元信息卡（渲染输入哈希/版本链/签发状态/双人签发位
             +pass.json 绑定复检）；
  ③同输入同输出钉  report-rerender——渲染纯函数跑两遍，两次哈希比对展示
             （pin_ok）；输入指纹变→输出哈希必变（防「假渲染」）；
  ④挂载层+页面层  /api/v2/* 全过会话门（缺会话=401 JSON，_V2MountHandler 钉
             include 挂法）；report-center.html 结构钉（两视图+四态+章节锚导航
             +重新渲染/下载/打印+零 CDN）。

状态机（确定性文件分类，零墙钟零 LLM）：
  已签发=report/signed/pass.json 在场（锁定+issued_at 时间戳）；
  待签发=有渲染工件（report/draft/*.md 或 findings.json）而无 pass.json；
  草稿  =其余（报告未聚合——仗打完数据在账，报告面待生成）。
版本链=report/signed/report-<ts>.md 逐版（文件名时间戳定序）；待签发=当前草稿版。
双签位=approvals.tsv decision=approved 行按时间序前两张卡（签发门 verify-signoff
人工批准在案的同源数据）；pass.json 在场=已锁定。
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from ledger import core  # noqa: E402
from ledger.norm import artifact_hashes  # noqa: E402
from webui import api_v2_reports as api  # noqa: E402

T = core.TABLES
TS1 = "2026-10-20T01:00:00Z"
TS2 = "2026-10-20T02:00:00Z"
TS3 = "2026-10-20T03:00:00Z"
TS4 = "2026-10-20T04:00:00Z"
TS5 = "2026-10-20T05:00:00Z"
TS6 = "2026-10-20T06:00:00Z"
TS7 = "2026-10-20T07:00:00Z"
AUTH_BYTES = b"AUTH-DOC report-center fixture\n"
ART1 = (b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        b"<html>admin orders</html>")
ART2 = b"5 login attempts in 10s"
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def row(tname, **kw):
    r = [""] * len(T[tname])
    for k, v in kw.items():
        r[T[tname].index(k)] = str(v)
    return r


def chained_tl(rows_spec):
    rows, prev = [], core.GENESIS
    for ts, actor, phase, event in rows_spec:
        wo = [ts, actor, phase, event, "", prev, "2"]
        h = core.row_hash(prev, wo)
        rows.append([ts, actor, phase, event, "", prev, h, "2"])
        prev = h
    return rows


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _writeb(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build_goal(gd, variant):
    """单 goal 夹具：13 表+工件+（按 variant）report 工件三态。

    variant: "signed"（双签+pass.json+两版签发稿）| "pending"（草稿已聚合
    待签发）| "draft"（无 report 目录——仗在打，报告未聚合）。
    """
    tag = os.path.basename(gd)[2:]            # G-t1 → t1
    os.makedirs(gd, exist_ok=True)
    auth_rel = "auth/G-%s-0001.pdf" % tag
    auth_sha = hashlib.sha256(AUTH_BYTES).hexdigest()
    _writeb(os.path.join(gd, auth_rel), AUTH_BYTES)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-%s-0001" % tag, target="shop-%s.example" % tag,
        objective="授权渗透：报告中心夹具", auth_doc=auth_rel, auth_sha256=auth_sha,
        signer="客户安全部", valid_from="2026-10-01T00:00:00Z",
        valid_until="2026-10-31T00:00:00Z", emergency_contact="oob@example.com",
        budget="2M;50000;40", business_context="凭据来源：客户提供",
        model_tier="strong", guard_tier="T3", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "scope.tsv"), [
        row("scope.tsv", id="S-%s-0001" % tag, kind="include",
            matcher="shop-%s.example" % tag, note="开战白名单",
            schema_version="2", created=TS1),
        row("scope.tsv", id="S-%s-0002" % tag, kind="include",
            matcher="api.shop-%s.example" % tag, schema_version="2", created=TS1),
        row("scope.tsv", id="S-%s-0003" % tag, kind="exclude",
            matcher="mail.shop-%s.example" % tag, note="邮件系统不测",
            schema_version="2", created=TS1),
        row("scope.tsv", id="S-%s-0004" % tag, kind="oob",
            matcher="10.0.0.0/8", note="内网段范围外", schema_version="2", created=TS1),
    ])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-%s-0001" % tag, title="管理面板未授权访问",
            detail="authz-diff", status="done", engine="web-blackbox",
            schema_version="2", created=TS1),
        row("intents.tsv", id="INT-%s-0002" % tag, title="登录面爆破探测",
            detail="rate-limit", status="pending", engine="web-blackbox",
            schema_version="2", created=TS2),
    ])
    h1r, h1n = artifact_hashes(ART1)
    h2r, h2n = artifact_hashes(ART2)
    ev1, ev2 = "EV-%s-0001" % tag, "EV-%s-0002" % tag
    fd1, fd2 = "FD-%s-0001" % tag, "FD-%s-0002" % tag
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id=fd1, intent_id="INT-%s-0001" % tag,
            title="管理面板匿名可读", confidence="C1", impact="高",
            exploitation_status="verified", dedup_key="admin-anon-read",
            scope_check="in_scope", description_brief="未登录可读取管理面板订单列表",
            affected_asset_id="AST-%s-0001" % tag, evidence_ids=",".join([ev1, ev2]),
            card_path="findings-cards/%s.md" % fd1, status="active",
            schema_version="2", created=TS2),
        row("findings.tsv", id=fd2, intent_id="INT-%s-0002" % tag,
            title="登录接口无速率限制", confidence="C2", impact="中",
            exploitation_status="suspected", dedup_key="login-no-ratelimit",
            scope_check="in_scope", description_brief="连续登录尝试无频控",
            affected_asset_id="AST-%s-0001" % tag,
            card_path="findings-cards/%s.md" % fd2, status="active",
            schema_version="2", created=TS3),
    ])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id=ev1, title="管理面板响应捕获", source_type="capture",
            observed_at=TS4, network_position="internet",
            repro_command="curl -i http://shop.example/admin", repro_kind="single",
            content_hash_raw=h1r, content_hash_norm=h1n,
            artifact_path="artifacts/%s.raw" % ev1, card_path="evidence/%s.md" % ev1,
            linked_finding=fd1, raw_excerpt="HTTP 200 admin",
            schema_version="2", created=TS4),
        row("E-index.tsv", id=ev2, title="登录爆破计数", source_type="command",
            observed_at=TS5, network_position="internet",
            repro_command="curl -X POST http://shop.example/login --data u=x",
            repro_kind="single", content_hash_raw=h2r, content_hash_norm=h2n,
            artifact_path="artifacts/%s.raw" % ev2, card_path="evidence/%s.md" % ev2,
            linked_finding=fd1, raw_excerpt="5 attempts",
            schema_version="2", created=TS5),
    ])
    core.write_tsv(os.path.join(gd, "matrix.tsv"), [
        row("matrix.tsv", attack_surface="web.admin-panel", vuln_class="authz.diff",
            state="x", reason="", intent_id="INT-%s-0001" % tag, schema_version="2",
            updated=TS2),
        row("matrix.tsv", attack_surface="web.login", vuln_class="authn.no-rate-limit",
            state="!", reason="budget-cap:预算止步于第 3 次探测",
            intent_id="INT-%s-0002" % tag, schema_version="2", updated=TS3),
        row("matrix.tsv", attack_surface="web.mail", vuln_class="config.misconfig",
            state="-", reason="oob:范围外（scope exclude 行在案）", schema_version="2",
            updated=TS3),
        row("matrix.tsv", attack_surface="web.api", vuln_class="inj.sql", state="",
            reason="", schema_version="2", updated=TS3),
        row("matrix.tsv", attack_surface="web.api", vuln_class="inj.xss", state="",
            reason="", schema_version="2", updated=TS3),
    ])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-%s-0001" % tag),
        (TS1, "总控", "P1", "add-scope S-%s-0001" % tag),
        (TS2, "CLI", "P2", "add-finding %s" % fd1),
        (TS3, "CLI", "P2", "add-finding %s" % fd2),
        (TS4, "CLI", "P2", "add-evidence %s" % ev1),
        (TS5, "CLI", "P2", "add-evidence %s" % ev2),
        (TS6, "复测岗", "P5", "replay-probe %s verdict=reproduced" % ev1),
    ]))
    ap_rows = []
    if variant in ("signed", "pending"):
        ap_rows.append(row("approvals.tsv", id="AP-%s-0001" % tag,
                           command_hash="a" * 64, decision="approved",
                           approver="操作员·wgen", timestamp=TS5,
                           note="报告签发第一签", schema_version="2"))
    if variant == "signed":
        ap_rows.append(row("approvals.tsv", id="AP-%s-0002" % tag,
                           command_hash="b" * 64, decision="approved",
                           approver="复核员·li", timestamp=TS6,
                           note="报告签发第二签（双人复核）", schema_version="2"))
    if ap_rows:
        core.write_tsv(os.path.join(gd, "approvals.tsv"), ap_rows)
    for tname in ("assets.tsv", "facts.tsv", "edges.tsv", "creds.tsv", "budget.tsv"):
        core.write_tsv(os.path.join(gd, tname), [])
    _writeb(os.path.join(gd, "artifacts", ev1 + ".raw"), ART1)
    _writeb(os.path.join(gd, "artifacts", ev2 + ".raw"), ART2)
    _write(os.path.join(gd, "evidence", ev1 + ".md"),
           "---\nid: %s\ntitle: 管理面板响应捕获\nsource_type: capture\n"
           "observed_at: %s\nraw_request: |\n  GET /admin HTTP/1.1\n"
           "  Host: shop.example\n---\n"
           "## 原始响应摘录（脱敏+定长）与判定依据\nHTTP 200 admin\n" % (ev1, TS4))
    _write(os.path.join(gd, "evidence", ev2 + ".md"),
           "---\nid: %s\ntitle: 登录爆破计数\nsource_type: command\n"
           "observed_at: %s\nraw_request: ''\n---\n"
           "## 原始响应摘录（脱敏+定长）与判定依据\n5 attempts\n" % (ev2, TS5))
    for fid in (fd1, fd2):
        _write(os.path.join(gd, "findings-cards", fid + ".md"),
               "---\nid: %s\ndedup_key: x\n---\n## 漏洞叙述\n叙述段。\n"
               "## 复现步骤\n引用 EV 卡。\n## 修复建议叙述\n（待 LLM 撰写）\n" % fid)
    if variant == "draft":
        return gd
    # 渲染工件：草稿（两 FD 段稿）+findings.json（pending/signed 共有）
    rdir = os.path.join(gd, "report")
    for fid in (fd1, fd2):
        _write(os.path.join(rdir, "draft", fid + ".md"),
               "## %s 九段渲染稿（夹具）\n段1\n" % fid)
    _write(os.path.join(rdir, "findings.json"), json.dumps(
        {"schema_version": "1.0", "goal": {"id": "G-%s-0001" % tag},
         "summary": {"total": 2, "verified": 1}}, ensure_ascii=False, indent=1))
    if variant == "pending":
        return gd
    # signed：两版签发稿+凭证（绑定哈希真值——复检得绿；篡改测试另有反例）
    arts = {"report/draft/%s.md" % fd1: _sha256_file(os.path.join(rdir, "draft", fd1 + ".md")),
            "report/draft/%s.md" % fd2: _sha256_file(os.path.join(rdir, "draft", fd2 + ".md")),
            "report/findings.json": _sha256_file(os.path.join(rdir, "findings.json"))}
    for ts in (TS5, TS6):
        fn = "report-%s.md" % ts.replace(":", "")
        _write(os.path.join(rdir, "signed", fn),
               "# 渗透测试报告终稿 · G-%s-0001\n签发时刻: %s\n（夹具签发稿）\n" % (tag, ts))
        arts["report/signed/" + fn] = _sha256_file(os.path.join(rdir, "signed", fn))
    gates = {k: {"status": "PASS", "detail": ""} for k in (
        "render", "nine_segments", "burp_pasteable", "dual_fingerprint",
        "time_chain", "authorization", "draft_byte_equal", "artifact_binding",
        "redact_scan", "cleanup_checklist", "tier_disclosure", "compliance_six",
        "empty_rhetoric", "aggregate", "terminal_b_disclosure")}
    cred = {"goal": "G-%s" % tag, "ts": TS6, "gates": gates, "artifacts": arts}
    _write(os.path.join(rdir, "signed", "pass.json"),
           json.dumps(cred, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
    return gd


def build_root(td):
    """battles 根夹具：battle-1 已签发 / battle-2 待签发 / battle-3 草稿。"""
    root = os.path.join(td, "battles")
    build_goal(os.path.join(root, "battle-1", "G-t1"), "signed")
    build_goal(os.path.join(root, "battle-2", "G-t2"), "pending")
    build_goal(os.path.join(root, "battle-3", "G-t3"), "draft")
    return root


def dir_bytes(path):
    out = {}
    for r, _d, files in os.walk(path):
        for n in sorted(files):
            p = os.path.join(r, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, path)] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.root = build_root(self.td.name)


# ═══════════════════════════════ ① 列表投影 ═══════════════════════════════

class TestReportListProjection(Base):
    """每仗一行：状态徽章（确定性文件分类）/版本数/最后渲染时间。"""

    def test_rows_one_per_battle_with_status(self):
        p = api.report_list_view(battles_dir=self.root)
        self.assertEqual([b["battle"] for b in p["battles"]],
                         ["battle-1", "battle-2", "battle-3"])
        st = {b["battle"]: b["status"] for b in p["battles"]}
        self.assertEqual(st, {"battle-1": "已签发", "battle-2": "待签发",
                              "battle-3": "草稿"})

    def test_row_fields_goal_and_findings(self):
        p = api.report_list_view(battles_dir=self.root)
        b1 = p["battles"][0]
        self.assertEqual(b1["goal"], "G-t1")
        self.assertEqual(b1["goal_id"], "G-t1-0001")
        self.assertEqual(b1["target"], "shop-t1.example")
        self.assertEqual(b1["findings"]["total"], 2)
        self.assertEqual(b1["findings"]["verified"], 1)
        self.assertTrue(b1["has_download"])
        b3 = p["battles"][2]
        self.assertEqual(b3["findings"]["total"], 2)
        self.assertFalse(b3["has_download"])      # 草稿：无渲染工件=无下载件

    def test_versions_count(self):
        p = api.report_list_view(battles_dir=self.root)
        v = {b["battle"]: b["versions"] for b in p["battles"]}
        self.assertEqual(v, {"battle-1": 2, "battle-2": 1, "battle-3": 0})

    def test_last_render_time(self):
        p = api.report_list_view(battles_dir=self.root)
        b1 = p["battles"][0]
        self.assertEqual(b1["last_render"], TS6)   # 最新签发稿文件名时间戳
        self.assertTrue(_ISO_RE.match(p["battles"][1]["last_render"] or ""))
        self.assertEqual(p["battles"][2]["last_render"], "")

    def test_status_counts_summary(self):
        p = api.report_list_view(battles_dir=self.root)
        self.assertEqual(p["counts"], {"signed": 1, "pending": 1, "draft": 1,
                                       "battles": 3})

    def test_empty_root_tolerant(self):
        p = api.report_list_view(battles_dir=os.path.join(self.td.name, "none"))
        self.assertEqual(p["battles"], [])
        self.assertEqual(p["counts"]["battles"], 0)

    def test_readonly_and_deterministic(self):
        before = dir_bytes(self.root)
        a = api.report_list_view(battles_dir=self.root)
        b = api.report_list_view(battles_dir=self.root)
        self.assertEqual(dir_bytes(self.root), before)
        self.assertEqual(a, b)
        json.dumps(a, ensure_ascii=False)          # 可序列化

    def test_goal_without_findings_tolerated(self):
        gd = os.path.join(self.root, "battle-4", "G-t4")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
            "goals.tsv", id="G-t4-0001", target="bare.example",
            schema_version="2", created=TS1)])
        p = api.report_list_view(battles_dir=self.root)
        b4 = [b for b in p["battles"] if b["battle"] == "battle-4"][0]
        self.assertEqual(b4["status"], "草稿")
        self.assertEqual(b4["findings"]["total"], 0)



# ═══════════════════════════════ ② 详情投影 ═══════════════════════════════

class TestReportDetailProjection(Base):
    """渲染预览六节+元信息卡（哈希/版本链/签发状态/双签位/绑定复检）。"""

    def gd(self, battle):
        return os.path.join(self.root, battle, {"battle-1": "G-t1",
                                                "battle-2": "G-t2",
                                                "battle-3": "G-t3"}[battle])

    def test_state_and_cover(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        self.assertEqual(p["goal"], "G-t1")
        self.assertEqual(p["battle"], {"id": "battle-1", "n": 1})
        self.assertEqual(p["state"]["status"], "已签发")
        self.assertTrue(p["state"]["locked"])
        self.assertEqual(p["state"]["issued_at"], TS6)
        cov = p["cover"]
        self.assertEqual(cov["report_no"], "G-t1-0001")
        self.assertEqual(cov["target"], "shop-t1.example")
        self.assertEqual(cov["signer"], "客户安全部")
        self.assertEqual(cov["valid_from"], "2026-10-01T00:00:00Z")
        self.assertEqual(cov["valid_until"], "2026-10-31T00:00:00Z")
        self.assertEqual(cov["budget"], "2M;50000;40")
        self.assertEqual(cov["guard_tier"], "T3")

    def test_authorization_summary(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        a = p["authorization"]
        self.assertEqual(a["auth_doc"], "auth/G-t1-0001.pdf")
        want = hashlib.sha256(AUTH_BYTES).hexdigest()
        self.assertEqual(a["auth_sha256"], want)
        self.assertEqual(a["sha_trunc"], want[:12])
        self.assertEqual(a["scope_counts"], {"include": 2, "exclude": 1, "oob": 1,
                                             "account-grant": 0})
        self.assertEqual(len(a["amendment_heads"]), 4)

    def test_findings_table_with_badges(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        rows = {f["id"]: f for f in p["findings"]["rows"]}
        self.assertEqual(rows["FD-t1-0001"]["impact"], "高")
        self.assertEqual(rows["FD-t1-0001"]["verify_state"], "已验证")
        self.assertIn("verified", rows["FD-t1-0001"]["verify_basis"])
        self.assertEqual(rows["FD-t1-0002"]["impact"], "中")
        self.assertEqual(rows["FD-t1-0002"]["verify_state"], "待验证")
        self.assertEqual(p["findings"]["counts"], {"total": 2, "verified": 1,
                                                   "pending": 1, "ruled_out": 0})

    def test_evidence_appendix(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        evs = p["evidence"]
        self.assertEqual([e["id"] for e in evs], ["EV-t1-0001", "EV-t1-0002"])
        self.assertEqual(evs[0]["hash_trunc"],
                         artifact_hashes(ART1)[0][:12])
        self.assertEqual(evs[0]["linked_finding"], "FD-t1-0001")

    def test_coverage_honesty(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        cov = p["coverage"]
        self.assertEqual(cov["tested"],
                         [{"attack_surface": "web.admin-panel",
                           "vuln_class": "authz.diff", "state": "x"}])
        un = {(u["attack_surface"], u["vuln_class"]): u for u in cov["untested"]}
        self.assertEqual(set(un), {("web.login", "authn.no-rate-limit"),
                                   ("web.mail", "config.misconfig"),
                                   ("web.api", "inj.sql"), ("web.api", "inj.xss")})
        self.assertEqual(un[("web.login", "authn.no-rate-limit")]["label"], "受阻")
        self.assertIn("预算止", un[("web.login", "authn.no-rate-limit")]["reason"])
        self.assertEqual(un[("web.mail", "config.misconfig")]["label"], "范围外")
        self.assertEqual(un[("web.api", "inj.sql")]["label"], "未测")
        self.assertEqual(cov["intents_open"], ["INT-t1-0002"])
        self.assertEqual(cov["closure"], "20.0%（1/5）")

    def test_methodology_appendix(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        m = p["methodology"]
        self.assertEqual(m["gates_passed"], [])
        self.assertEqual(m["intents_open"], 1)
        self.assertEqual(m["intents_closed"], 1)
        self.assertEqual(m["budget_terminal"], "normal")
        self.assertEqual(m["guard_tier"], "T3")
        self.assertEqual(m["timeline_rows"], 7)
        self.assertTrue(m["chain_ok"])

    def test_meta_input_hash_and_pin(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        meta = p["meta"]
        self.assertRegex(meta["input_hash"], r"^[0-9a-f]{64}$")
        self.assertGreater(meta["input_files"], 10)
        self.assertEqual(len(meta["render_runs"]), 2)
        self.assertEqual(meta["render_runs"][0], meta["render_runs"][1])
        self.assertTrue(meta["pin_ok"])
        self.assertEqual(meta["render_hash"], meta["render_runs"][0])
        self.assertEqual(meta["output_chars"], len(p["markdown"]))
        self.assertEqual(meta["render_hash"],
                         hashlib.sha256(p["markdown"].encode("utf-8")).hexdigest())

    def test_markdown_projection_sections(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        md = p["markdown"]
        for head in ("# 渗透测试报告", "## 授权与范围", "## 发现明细",
                     "## 证据附录", "## 覆盖诚实", "## 方法论"):
            self.assertIn(head, md)
        self.assertIn("shop-t1.example", md)
        self.assertIn("FD-t1-0001", md)
        self.assertIn("EV-t1-0001", md)

    def test_version_chain_signed(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        vs = p["meta"]["versions"]
        self.assertEqual([v["v"] for v in vs], [1, 2])
        self.assertTrue(all(v["kind"] == "signed" for v in vs))
        self.assertEqual(vs[0]["ts"], TS5)
        self.assertEqual(vs[1]["ts"], TS6)
        self.assertEqual(vs[1]["sha256"],
                         _sha256_file(os.path.join(self.gd("battle-1"),
                                                   vs[1]["file"])))

    def test_version_chain_pending_draft(self):
        p = api.report_detail_view(battles_dir=self.root, battle=2)
        vs = p["meta"]["versions"]
        self.assertEqual(len(vs), 1)
        self.assertEqual(vs[0]["kind"], "draft")
        self.assertEqual(p["state"]["status"], "待签发")

    def test_signature_cards_dual(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        sigs = p["meta"]["signatures"]
        self.assertEqual(len(sigs), 2)
        self.assertTrue(all(s["filled"] for s in sigs))
        self.assertEqual(sigs[0]["approver"], "操作员·wgen")
        self.assertEqual(sigs[1]["approver"], "复核员·li")
        self.assertTrue(p["meta"]["dual_complete"])

    def test_signature_cards_pending_single(self):
        p = api.report_detail_view(battles_dir=self.root, battle=2)
        sigs = p["meta"]["signatures"]
        self.assertTrue(sigs[0]["filled"])
        self.assertFalse(sigs[1]["filled"])
        self.assertFalse(p["meta"]["dual_complete"])

    def test_credential_binding_ok(self):
        p = api.report_detail_view(battles_dir=self.root, battle=1)
        c = p["meta"]["credential"]
        self.assertEqual(c["ts"], TS6)
        self.assertTrue(c["gates_pass"])
        self.assertEqual(c["artifacts"], 5)
        self.assertTrue(c["binding_ok"])
        self.assertEqual(c["bad"], [])

    def test_credential_binding_tamper_detected(self):
        root2 = os.path.join(self.td.name, "b2")
        shutil.copytree(self.root, root2)
        tgt = os.path.join(root2, "battle-1", "G-t1", "report", "signed",
                           "report-2026-10-20T060000Z.md")
        with open(tgt, "ab") as f:
            f.write(b"tampered")
        p = api.report_detail_view(battles_dir=root2, battle=1)
        self.assertFalse(p["meta"]["credential"]["binding_ok"])
        self.assertTrue(p["meta"]["credential"]["bad"])
        self.assertEqual(p["state"]["status"], "已签发")     # 锁定不因篡改回退

    def test_draft_state_full_shape(self):
        p = api.report_detail_view(battles_dir=self.root, battle=3)
        self.assertEqual(p["state"]["status"], "草稿")
        self.assertFalse(p["state"]["locked"])
        self.assertEqual(p["meta"]["versions"], [])
        self.assertEqual(len(p["findings"]["rows"]), 2)      # 发现仍在（账面）
        self.assertTrue(p["meta"]["pin_ok"])                 # 草稿同钉渲染

    def test_goal_param_resolves_within_battles_root(self):
        p = api.report_detail_view(battles_dir=self.root, goal="G-t2")
        self.assertEqual(p["goal"], "G-t2")
        self.assertEqual(p["battle"], {"id": "battle-2", "n": 2})

    def test_goal_param_falls_back_to_ledger_dir(self):
        gd3 = os.path.join(self.td.name, "G-solo")
        build_goal(gd3, "pending")
        p = api.report_detail_view(battles_dir=self.root, goal="G-solo",
                                   ledger_dir=gd3)
        self.assertEqual(p["goal"], "G-solo")
        self.assertIsNone(p["battle"])

    def test_404_422_400_shapes(self):
        st, out = api.report_detail_route({"battle": "99"}, None, self.root)
        self.assertEqual(st, 404)
        self.assertIn("error", out)
        self.assertIn("battles", out)
        st, _ = api.report_detail_route({"battle": "abc"}, None, self.root)
        self.assertEqual(st, 422)
        st, _ = api.report_detail_route({}, None, self.root)
        self.assertEqual(st, 400)

    def test_readonly_and_deterministic(self):
        before = dir_bytes(self.root)
        a = api.report_detail_view(battles_dir=self.root, battle=1)
        b = api.report_detail_view(battles_dir=self.root, battle=1)
        self.assertEqual(dir_bytes(self.root), before)
        self.assertEqual(a, b)


class TestRenderPin(Base):
    """同输入同输出钉：渲染纯函数两跑逐字节一致；输入动→哈希动。"""

    def test_two_runs_identical(self):
        gd = os.path.join(self.root, "battle-1", "G-t1")
        pin = api.render_pin(gd)
        self.assertEqual(pin["render_runs"][0], pin["render_runs"][1])
        self.assertTrue(pin["pin_ok"])
        self.assertEqual(pin["render_hash"], pin["render_runs"][0])

    def test_input_change_moves_both_hashes(self):
        gd = os.path.join(self.root, "battle-1", "G-t1")
        before = api.render_pin(gd)
        rows = core.Session(gd).rows("goals.tsv")
        rows[-1][T["goals.tsv"].index("target")] = "shop-t1-renamed.example"
        core.write_tsv(os.path.join(gd, "goals.tsv"), rows)
        after = api.render_pin(gd)
        self.assertNotEqual(after["input_hash"], before["input_hash"])
        self.assertNotEqual(after["render_hash"], before["render_hash"])
        self.assertTrue(after["pin_ok"])                     # 动后仍自一致

    def test_readonly(self):
        gd = os.path.join(self.root, "battle-1", "G-t1")
        before = dir_bytes(gd)
        api.render_pin(gd)
        self.assertEqual(dir_bytes(gd), before)


if __name__ == "__main__":
    unittest.main()
