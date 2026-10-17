# -*- coding: utf-8 -*-
"""T1·P6 漏洞详情完整版——五区全量页钉测（界面线施工计划 2026-10-18 T1）。

python3 -m unittest tests.test_webui_pagespec_finding_detail
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P6；文案宪法#41（界面人话律）。

三层钉：
  ①投影层  api_v2_findings.finding_detail/evidence_raw——五区数据单源
           （findings+E-index+timeline+replay/*.json+卡片 过滤投影）；
  ②挂载层  api_pages.py 未落地（UI-1 在飞）——以 Handler 子类钉 include 挂法：
           /api/v2/* 全过会话门（无 cookie=401 JSON），分发给 ROUTES 单源表；
  ③页面层  static/pages/finding-detail.html 结构钉（五区 id+四态+雷达 SVG+
           抽屉/全屏两形态+nav.push 自注册+零 CDN）。
"""
import json
import os
import shutil
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from ledger import core  # noqa: E402
from ledger.norm import artifact_hashes  # noqa: E402
from webui import api_v2_findings as api  # noqa: E402
from webui import server as srv_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-18T01:00:00Z"
TS1B = "2026-10-18T01:10:00Z"
TS2 = "2026-10-18T02:00:00Z"
TS3 = "2026-10-18T03:00:00Z"
TS4 = "2026-10-18T04:00:00Z"
TS5 = "2026-10-18T05:00:00Z"
TS6 = "2026-10-18T06:00:00Z"
VEC = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"      # 经典 9.1 向量
ART1 = (b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nSet-Cookie: sid=x\r\n\r\n"
        b"<html>admin orders</html>")
ART2 = b"5 login attempts in 10s"


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


def build_fixture(td):
    """P6 夹具：1 条已验证发现(卡+双证据+三次重放含自动复测)+1 条候选发现(无证据)。"""
    gd = os.path.join(td, "G-t1")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-t1-0001", intent_id="INT-t1-0001",
            title="管理面板匿名可读", confidence="C1", impact="高",
            exploitation_status="verified", dedup_key="admin-anon-read",
            vuln_ref="CVE-2026-1337", scope_check="in_scope",
            description_brief="未登录可读取管理面板订单列表",
            reproducible_steps="1) GET /admin 2) 观察订单数据", affected_asset_id="AST-t1-0001",
            evidence_ids="EV-t1-0001,EV-t1-0002", card_path="findings-cards/FD-t1-0001.md",
            status="active", schema_version="2", created=TS1),
        row("findings.tsv", id="FD-t1-0002", intent_id="INT-t1-0001",
            title="登录接口无速率限制", confidence="C2", impact="中",
            exploitation_status="suspected", dedup_key="login-no-ratelimit",
            scope_check="in_scope", description_brief="连续登录尝试无频控",
            affected_asset_id="AST-t1-0001", card_path="findings-cards/FD-t1-0002.md",
            status="active", schema_version="2", created=TS1B),
    ])
    h1r, h1n = artifact_hashes(ART1)
    h2r, h2n = artifact_hashes(ART2)
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id="EV-t1-0001", title="管理面板响应捕获",
            source_type="capture", observed_at=TS2, network_position="internet",
            repro_command="curl -i http://shop.example/admin", repro_kind="single",
            content_hash_raw=h1r, content_hash_norm=h1n,
            artifact_path="artifacts/EV-t1-0001.raw", card_path="evidence/EV-t1-0001.md",
            linked_finding="FD-t1-0001", raw_excerpt="HTTP 200 admin",
            schema_version="2", created=TS2),
        row("E-index.tsv", id="EV-t1-0002", title="登录爆破计数", source_type="command",
            observed_at=TS3, network_position="internet",
            repro_command="curl -X POST http://shop.example/login --data u=x",
            repro_kind="single", content_hash_raw=h2r, content_hash_norm=h2n,
            artifact_path="artifacts/EV-t1-0002.raw", card_path="evidence/EV-t1-0002.md",
            linked_finding="FD-t1-0001", raw_excerpt="5 attempts",
            schema_version="2", created=TS3),
    ])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-finding FD-t1-0001"),
        (TS1B, "总控", "P0", "add-finding FD-t1-0002"),
        (TS2, "CLI", "P2", "add-evidence EV-t1-0001"),
        (TS3, "CLI", "P2", "add-evidence EV-t1-0002"),
        (TS4, "CLI", "P2", "replay-probe EV-t1-0001 verdict=not-reproduced"),
        (TS5, "复测岗", "P5", "replay-probe EV-t1-0001 verdict=reproduced"),
        (TS6, "CLI", "P2", "replay-probe EV-t1-0002 verdict=reproduced"),
    ]))
    for ev, data in (("EV-t1-0001", ART1), ("EV-t1-0002", ART2)):
        p = os.path.join(gd, "artifacts", ev + ".raw")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
    _write(os.path.join(gd, "findings-cards", "FD-t1-0001.md"),
           "---\nid: FD-t1-0001\ndedup_key: admin-anon-read\nscope_check: in_scope\n"
           "exploitation_status: verified\nconfidence: C1\nimpact: 高\nauth_context: \n"
           "evidence_ids: [EV-t1-0001, EV-t1-0002]\ncontrol_evidence_ids: []\n"
           "affected_asset_id: AST-t1-0001\npair_group: \n"
           "cvss_vector: '" + VEC + "'\n---\n"
           "## 漏洞叙述\n管理面板路由缺会话校验中间件，匿名请求直达订单数据接口。\n"
           "## 复现步骤\n引用 EV-t1-0001 卡片四要素。\n"
           "## 修复建议叙述\n根因: admin 路由未挂会话校验中间件\n"
           "代码位: routes/admin.py:42\n修复后验证: curl -i http://shop.example/admin 应 302\n")
    _write(os.path.join(gd, "findings-cards", "FD-t1-0002.md"),
           "---\nid: FD-t1-0002\ndedup_key: login-no-ratelimit\n---\n"
           "## 漏洞叙述\n（待 LLM 撰写，只能引用账本已有数据）\n"
           "## 复现步骤\n（引用 EV 卡片 POC 四要素，不复制原文）\n"
           "## 修复建议叙述\n（待 LLM 撰写）\n")
    _write(os.path.join(gd, "evidence", "EV-t1-0001.md"),
           "---\nid: EV-t1-0001\ntitle: 管理面板响应捕获\nsource_type: capture\n"
           "observed_at: " + TS2 + "\nnetwork_position: internet\npreconditions: []\n"
           "raw_request: |\n  GET /admin HTTP/1.1\n  Host: shop.example\n  \n"
           "expected: {}\ncleanup: ''\npair_group: \nrole: \n---\n"
           "## 原始响应摘录（脱敏+定长）与判定依据\nHTTP 200 admin\n")
    _write(os.path.join(gd, "evidence", "EV-t1-0002.md"),
           "---\nid: EV-t1-0002\ntitle: 登录爆破计数\nsource_type: command\n"
           "observed_at: " + TS3 + "\nnetwork_position: internet\npreconditions: []\n"
           "raw_request: ''\nexpected: {}\ncleanup: ''\npair_group: \nrole: \n---\n"
           "## 原始响应摘录（脱敏+定长）与判定依据\n5 attempts\n")
    _replay(gd, "EV-t1-0001", 1, {"id": "EV-t1-0001", "verdict": "not-reproduced",
                                  "matched": False, "status": 200})
    _replay(gd, "EV-t1-0001", 2, {"id": "EV-t1-0001", "verdict": "reproduced",
                                  "matched": True, "status": 200, "elapsed_ms": 1250})
    _replay(gd, "EV-t1-0002", 1, {"id": "EV-t1-0002", "verdict": "reproduced",
                                  "matched": True, "status": 200})
    return gd


def _replay(gd, ev, seq, obj):
    d = os.path.join(gd, "replay", ev)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "%d.json" % seq), "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True)


def dir_bytes(gd):
    out = {}
    for root, _dirs, files in os.walk(gd):
        for n in sorted(files):
            p = os.path.join(root, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, gd)] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_fixture(self.td.name)


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestFindingDetailProjection(Base):
    """五区数据单源：头区/CVSS/验证态+修复建议+证据卡+重放史+生命线。"""

    def test_head_zone_fields(self):
        st, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertEqual(st, 200)
        f = p["finding"]
        self.assertEqual(f["id"], "FD-t1-0001")
        self.assertEqual(f["title"], "管理面板匿名可读")
        self.assertEqual(f["impact"], "高")
        self.assertEqual(f["vuln_ref"], "CVE-2026-1337")
        self.assertEqual(f["status"], "active")
        self.assertEqual(p["goal"], "G-t1")

    def test_cvss_score_from_vector_card(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertEqual(p["cvss"]["vector"], VEC)
        self.assertEqual(p["cvss"]["score"], 9.1)          # 经典向量官方分
        self.assertFalse(p["cvss"]["pending"])
        self.assertEqual(p["cvss"]["source"], "finding-card")

    def test_cvss_pending_without_vector(self):
        _, p = api.finding_detail({"id": "FD-t1-0002"}, self.gd)
        self.assertTrue(p["cvss"]["pending"])
        self.assertIsNone(p["cvss"]["score"])
        self.assertEqual(p["cvss"]["vector"], "")

    def test_verification_and_retest_states(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertEqual(p["verification"]["state"], "已验证")
        self.assertEqual(p["retest"]["runs"], 3)           # 两条 EV 共 3 次重放
        self.assertEqual(p["retest"]["state"], "复测完成·漏洞仍存在")
        self.assertEqual(p["retest"]["last_at"], TS6)
        _, p2 = api.finding_detail({"id": "FD-t1-0002"}, self.gd)
        self.assertEqual(p2["verification"]["state"], "待验证")
        self.assertEqual(p2["retest"]["state"], "未复测")
        self.assertEqual(p2["retest"]["runs"], 0)

    def test_description_and_fix_subcard(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertIn("未登录", p["finding"]["description_brief"])
        self.assertIn("中间件", p["tech_desc"])
        fix = p["fix"]
        self.assertTrue(fix["written"])
        self.assertEqual(fix["root_cause"], "admin 路由未挂会话校验中间件")
        self.assertEqual(fix["code_location"], "routes/admin.py:42")
        self.assertEqual(fix["verify_command"], "curl -i http://shop.example/admin 应 302")
        self.assertEqual(fix["fallback_commands"],
                         ["curl -i http://shop.example/admin",
                          "curl -X POST http://shop.example/login --data u=x"])

    def test_fix_unwritten_shows_pending(self):
        _, p = api.finding_detail({"id": "FD-t1-0002"}, self.gd)
        self.assertFalse(p["fix"]["written"])
        self.assertEqual(p["fix"]["root_cause"], "")

    def test_evidence_cards_zone(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        evs = p["evidence"]
        self.assertEqual([e["id"] for e in evs], ["EV-t1-0001", "EV-t1-0002"])
        e1 = evs[0]
        self.assertEqual(e1["source_type"], "capture")
        self.assertEqual(e1["observed_at"], TS2)
        self.assertEqual(e1["hash_trunc"], e1["content_hash_raw"][:12])
        self.assertEqual(len(e1["hash_trunc"]), 12)
        self.assertEqual(e1["verdict"], "reproduced")       # 最新 replay-probe 行
        self.assertTrue(e1["has_request"])                  # 卡片 raw_request 在
        self.assertTrue(e1["hash_ok"])                      # 工件重算==在册
        self.assertTrue(evs[1]["hash_ok"])

    def test_replay_history_zone(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        rs = p["replays"]
        self.assertEqual(len(rs), 3)
        self.assertEqual([r["seq"] for r in rs], [1, 2, 3])
        self.assertEqual(rs[0]["at"], TS4)
        self.assertEqual(rs[0]["verdict"], "not-reproduced")
        self.assertEqual(rs[0]["trigger"], "手动")
        self.assertIsNone(rs[0]["duration_ms"])             # 未记录耗时=空
        self.assertEqual(rs[1]["trigger"], "自动复测")       # 复测岗=自动
        self.assertEqual(rs[1]["duration_ms"], 1250)        # replay JSON elapsed_ms
        self.assertEqual(rs[2]["ev_id"], "EV-t1-0002")
        self.assertEqual(rs[2]["verdict"], "reproduced")

    def test_lifeline_zone(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        lf = p["lifeline"]
        kinds = [e["kind"] for e in lf]
        self.assertEqual(kinds[0], "first")
        self.assertIn("replay", kinds)
        self.assertIn("retest", kinds)                      # 自动复测独立节点
        self.assertEqual(kinds[-1], "current")
        first = lf[0]
        self.assertEqual(first["at"], TS1)
        cur = lf[-1]
        self.assertIn("已验证", cur["label"])

    def test_chain_integrity_green(self):
        _, p = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertTrue(p["chain"]["ok"])
        names = [c["name"] for c in p["chain"]["checks"]]
        self.assertIn("账本时间链", names)
        self.assertTrue(any(n.startswith("证据哈希 ") for n in names))   # 逐卡粒度
        self.assertTrue(all(n != "证据引用" for n in names))            # 引用全闭合

    def test_chain_integrity_red_on_artifact_tamper(self):
        gd2 = os.path.join(self.td.name, "G-tamper")
        shutil.copytree(self.gd, gd2)
        p2 = os.path.join(gd2, "artifacts", "EV-t1-0001.raw")
        with open(p2, "ab") as f:
            f.write(b"tampered")
        _, out = api.finding_detail({"id": "FD-t1-0001"}, gd2)
        self.assertFalse(out["chain"]["ok"])
        bad = [c for c in out["chain"]["checks"] if not c["ok"]]
        self.assertTrue(any("EV-t1-0001" in c["name"] for c in bad))
        ev = {e["id"]: e for e in out["evidence"]}
        self.assertFalse(ev["EV-t1-0001"]["hash_ok"])

    def test_empty_finding_tolerant(self):
        gd = os.path.join(self.td.name, "G-bare")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "findings.tsv"), [row(
            "findings.tsv", id="FD-b1-0001", title="裸发现", impact="低",
            status="active", created=TS1)])
        st, p = api.finding_detail({"id": "FD-b1-0001"}, gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["evidence"], [])
        self.assertEqual(p["replays"], [])
        self.assertTrue(p["cvss"]["pending"])
        self.assertTrue(p["chain"]["ok"])
        kinds = [e["kind"] for e in p["lifeline"]]
        self.assertEqual(kinds, ["first", "current"])

    def test_404_and_400_shapes(self):
        st, p = api.finding_detail({"id": "FD-nope"}, self.gd)
        self.assertEqual(st, 404)
        self.assertIn("error", p)
        st, p = api.finding_detail({}, self.gd)
        self.assertEqual(st, 400)
        self.assertIn("error", p)
        st, p = api.finding_detail({"id": "FD-t1-0001"}, os.path.join(self.td.name, "G-none"))
        self.assertEqual(st, 404)

    def test_readonly_deterministic_json(self):
        before = dir_bytes(self.gd)
        a = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        b = api.finding_detail({"id": "FD-t1-0001"}, self.gd)
        self.assertEqual(dir_bytes(self.gd), before)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a[1], ensure_ascii=False), str)

    def test_goal_param_resolves_sibling(self):
        alt = os.path.join(self.td.name, "G-alt")
        os.makedirs(alt)
        core.write_tsv(os.path.join(alt, "findings.tsv"), [row(
            "findings.tsv", id="FD-a1-0001", title="邻位发现", impact="低",
            status="active", created=TS1)])
        st, p = api.finding_detail({"id": "FD-a1-0001", "goal": "G-alt"}, self.gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["finding"]["title"], "邻位发现")


class TestEvidenceRawProjection(Base):
    """证据区「查看原始报文」懒载投影：请求响应对(mono)+仅头/全文两档。"""

    def test_http_pair_head_and_full(self):
        st, p = api.evidence_raw({"id": "EV-t1-0001"}, self.gd)
        self.assertEqual(st, 200)
        self.assertTrue(p["has_request"])
        self.assertTrue(p["request"].startswith("GET /admin HTTP/1.1"))
        self.assertIn("Host: shop.example", p["request"])
        resp = p["response"]
        self.assertTrue(resp["is_http"])
        self.assertIn("HTTP/1.1 200 OK", resp["head"])
        self.assertIn("Set-Cookie: sid=x", resp["head"])
        self.assertNotIn("<html>", resp["head"])           # 仅头=无正文
        self.assertIn("<html>admin orders</html>", resp["full"])
        self.assertTrue(p["hash_ok"])

    def test_non_http_artifact(self):
        st, p = api.evidence_raw({"id": "EV-t1-0002"}, self.gd)
        self.assertEqual(st, 200)
        self.assertFalse(p["has_request"])
        self.assertFalse(p["response"]["is_http"])
        self.assertEqual(resp_text(p), "5 login attempts in 10s")

    def test_404_and_400(self):
        st, _ = api.evidence_raw({"id": "EV-nope"}, self.gd)
        self.assertEqual(st, 404)
        st, _ = api.evidence_raw({}, self.gd)
        self.assertEqual(st, 400)

    def test_readonly(self):
        before = dir_bytes(self.gd)
        api.evidence_raw({"id": "EV-t1-0001"}, self.gd)
        self.assertEqual(dir_bytes(self.gd), before)


def resp_text(p):
    return p["response"]["full"]


class TestCvssEvidenceFallback(Base):
    """cycle② 向量兜底律（UI-1 实勘：findings 行无 CVSS 向量字段）。

    向量在场（描述/复现/证据原文含 CVSS:3.1/…）才实算并示向量+雷达；
    否则等级=真实 impact 高中低、向量区诚实示「待评定」——禁虚构向量。
    优先序：发现卡 front-matter → 发现卡正文 → 证据原文（工件+摘录）。
    """

    VEC_EV = "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:L/A:N"

    def _attach(self, art, excerpt=""):
        """给 FD-t1-0002（卡无向量）挂一条携带文本的证据工件。"""
        gd = os.path.join(self.td.name, "G-cvss")
        shutil.copytree(self.gd, gd)
        ev = "EV-t2-0001"
        p = os.path.join(gd, "artifacts", ev + ".raw")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(art)
        hraw, hnorm = artifact_hashes(art)
        rows = core.Session(gd).rows("E-index.tsv")
        rows.append(row("E-index.tsv", id=ev, title="向量携带证据", source_type="capture",
                        observed_at=TS4, network_position="internet",
                        repro_command="", repro_kind="single",
                        content_hash_raw=hraw, content_hash_norm=hnorm,
                        artifact_path="artifacts/" + ev + ".raw",
                        card_path="evidence/" + ev + ".md",
                        linked_finding="FD-t1-0002", raw_excerpt=excerpt,
                        schema_version="2", created=TS4))
        core.write_tsv(os.path.join(gd, "E-index.tsv"), rows)
        _write(os.path.join(gd, "evidence", ev + ".md"),
               "---\nid: " + ev + "\ntitle: 向量携带证据\nsource_type: capture\n"
               "observed_at: " + TS4 + "\nraw_request: ''\n---\n"
               "## 原始响应摘录（脱敏+定长）与判定依据\nscanner\n")
        return gd

    def test_vector_from_evidence_artifact(self):
        gd = self._attach(b"scanner: risk high, vector " + self.VEC_EV.encode() +
                          b" (auto-scored)")
        st, p = api.finding_detail({"id": "FD-t1-0002"}, gd)
        self.assertEqual(st, 200)
        self.assertEqual(p["cvss"]["vector"], self.VEC_EV)
        self.assertEqual(p["cvss"]["source"], "evidence-raw")
        self.assertIsNotNone(p["cvss"]["score"])
        self.assertFalse(p["cvss"]["pending"])

    def test_vector_from_evidence_excerpt(self):
        gd = self._attach(b"plain artifact text", excerpt="评级依据 " + self.VEC_EV)
        _, p = api.finding_detail({"id": "FD-t1-0002"}, gd)
        self.assertEqual(p["cvss"]["vector"], self.VEC_EV)
        self.assertEqual(p["cvss"]["source"], "evidence-raw")
        self.assertFalse(p["cvss"]["pending"])

    def test_binary_artifact_tolerated_no_vector(self):
        gd = self._attach(b"\xff\xfe\x00\x01\x80binary-blob-no-vector")
        st, p = api.finding_detail({"id": "FD-t1-0002"}, gd)
        self.assertEqual(st, 200)                            # 非法 utf-8 不炸
        self.assertTrue(p["cvss"]["pending"])                # 无向量=待评定（禁虚构）
        self.assertEqual(p["cvss"]["vector"], "")
        self.assertEqual(p["finding"]["impact"], "中")      # 等级=真实 impact

    def test_card_vector_wins_over_evidence(self):
        gd = self._attach(b"CVSS:3.1/AV:P/AC:H/PR:H/UI:R/S:U/C:L/I:L/A:N")
        _, p = api.finding_detail({"id": "FD-t1-0001"}, gd)
        self.assertEqual(p["cvss"]["source"], "finding-card")
        self.assertEqual(p["cvss"]["vector"], VEC)
        self.assertEqual(p["cvss"]["score"], 9.1)           # 卡向量优先


# ═══════════════════════════════ ② 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（api_pages.py 未落地）：/api/v2/* 过会话门后分发 ROUTES。

    UI-1 的 api_pages.py 落地时按本形挂载即可：会话门复用 Handler._session_ok，
    分发=api_v2_findings.ROUTES[path](query, ledger_dir) → (status, payload)。
    """

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path in api.ROUTES:
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            status, payload = api.ROUTES[u.path](q, self.server.ledger_dir)
            return self._send(status, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class ServerBase(Base):
    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), _V2MountHandler,
                                     ledger_dir=self.gd,
                                     operator_key=webui_login.OP_KEY)
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)
        self.sid = webui_login.login(self.port)

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _get(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()


class TestV2MountContract(ServerBase):
    """/api/v2/* 会话门+分发（动态口=server_address[1]，禁碰 8900）。"""

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/finding-detail?id=FD-t1-0001", cookie=False)
        self.assertEqual(resp.status, 401)
        self.assertEqual(json.loads(resp.read().decode("utf-8"))["error"],
                         "未登录或会话过期——读面须操作员会话")
        conn.close()

    def test_detail_over_http(self):
        conn, resp = self._get("/api/v2/finding-detail?id=FD-t1-0001")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["finding"]["id"], "FD-t1-0001")
        self.assertEqual(p["cvss"]["score"], 9.1)
        conn.close()

    def test_evidence_raw_over_http(self):
        conn, resp = self._get("/api/v2/evidence-raw?id=EV-t1-0001")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(p["response"]["is_http"])
        conn.close()

    def test_unknown_id_404_over_http(self):
        conn, resp = self._get("/api/v2/finding-detail?id=FD-nope")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_unknown_v2_path_falls_through_404(self):
        conn, resp = self._get("/api/v2/nope")
        self.assertEqual(resp.status, 404)
        conn.close()

    def test_http_hits_readonly(self):
        before = dir_bytes(self.gd)
        for pth in ("/api/v2/finding-detail?id=FD-t1-0001",
                    "/api/v2/evidence-raw?id=EV-t1-0002"):
            conn, resp = self._get(pth)
            self.assertEqual(resp.status, 200, pth)
            resp.read()
            conn.close()
        self.assertEqual(dir_bytes(self.gd), before)

# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

PAGE = os.path.join(CLI, "webui", "static", "pages", "finding-detail.html")
ZONE_MARKS = (
    # 五区容器
    'id="zone-head"', 'id="zone-desc"', 'id="zone-evidence"',
    'id="zone-replay"', 'id="zone-lifeline"',
    # 头区：徽章/CVSS/向量雷达/验证态/重放钮/复测态
    'id="sev-badge"', 'id="cvss-score"', 'id="cvss-vector"', 'id="cvss-radar"',
    'id="verify-badge"', 'id="btn-replay"', 'id="retest-status"',
    # 描述区：一句话结论/技术描述/修复建议子卡
    'id="fd-brief"', 'id="fd-tech"', 'id="fix-card"', 'id="fix-root"',
    'id="fix-code"', 'id="fix-verify"', 'id="btn-copy-verify"',
    # 证据区：EV 卡列表/链完整性
    'id="ev-list"', 'id="chain-bar"', 'id="chain-broken"',
    # 重放史区
    'id="replay-table"',
    # 生命线区
    'id="lifeline"',
    # 四态（空/加载/错误含重试/正常）
    'id="st-empty"', 'id="st-loading"', 'id="st-error"', 'id="btn-retry"',
    'id="st-normal"',
    # 两形态（抽屉/全屏）+ 宿主壳接入
    "mode-drawer", "mode-full", "FindingDetail",
    # 零框架自绘雷达
    "createElementNS",
    # 响应切换 仅头/全文
    "仅头", "全文",
    # CVSS 官方计算器链接（spec P6 交互）
    "first.org/cvss/calculator",
    # 立即重放按钮的写入尝试 + 失败降级
    "/api/v2/finding/replay",
    # 复制能力（哈希截断+复制/验证命令复制/报文复制）
    "copyText",
)
FETCH_MARKS = ("'/api/v2/finding-detail", "'/api/v2/evidence-raw")


class TestPageStructure(Base):
    def _src(self):
        with open(PAGE, encoding="utf-8") as f:
            return f.read()

    def test_five_zones_and_states_present(self):
        src = self._src()
        for m in ZONE_MARKS:
            self.assertIn(m, src, "缺 " + m)
        for m in FETCH_MARKS:
            self.assertIn(m, src, "须拉取 " + m)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'finding-detail'", src)
        self.assertIn("group: '发现'", src)
        self.assertIn("typeof nav.push", src)               # 壳未落也不炸

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertEqual(src.count("https://"), 1, "唯一外链=CVSS 官方计算器")
        self.assertIn("https://www.first.org/cvss/calculator", src)

    def test_ask_ai_anchor_placeholder(self):
        """「问 AI」按钮位：锚定对话设计已入库（contextual-chat-v1）——只留锚点不实现。

        锚=账本行址（表+行号+行哈希）；本页以 data-anchor-* 携带发现行址；
        点击仅出占位说明，零对话请求（对话面板 W6 落地后接壳常驻面板）。
        """
        src = self._src()
        self.assertIn('id="btn-ask-ai"', src)
        self.assertIn("问 AI", src)                          # 文案=设计档原词
        self.assertIn('data-anchor-table="findings.tsv"', src)
        self.assertIn("data-anchor-id", src)
        self.assertIn("锚定对话", src)                       # 占位说明明示排期
        self.assertNotIn("api/v2/ask", src)                 # 留锚点≠实现：零请求

    def test_js_under_2000_lines_page_over_600(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)
        self.assertGreaterEqual(len(src.splitlines()), 600, "P6 全量页 ~700 行量纲")

if __name__ == "__main__":
    unittest.main()
