# -*- coding: utf-8 -*-
"""图升级批·数据段（2026-10-16 计划）——graph 投影节点 ARTEX 式富卡。

python3 -m unittest tests.test_graph_rich
律（docs/superpowers/plans/2026-10-16-graph-upgrade.md 数据段 + 投影律）：
只读零写入、纯 stdlib、3.9 兼容、确定性（全取文件序）。
钉：卡片字段齐（num/kind/badge/title/status/layer + 兼容旧字段）/
编号全图唯一（按类型计数 T1/I3/F12/V7 式）/title 规则（意图=目的原文前120字、
发现=完整标题、事实=摘要前80字、其余=id+简述）/status 三态（未证实=candidate
或终态未证成，淡显标记）/impact 仅发现/事件溯源 latest-wins（同 id 追加行取最新）
/边保持 10 型+标签/向后兼容（test_v09b_pages 的 id/label/candidate/layer 语义不变）。
"""
import json, os, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from ledger import core  # noqa: E402
from ledger.write_cmds import EDGE_KINDS  # noqa: E402

from webui import projections as proj_mod  # noqa: E402

T = core.TABLES
TS1 = "2026-10-16T01:00:00Z"
TS2 = "2026-10-16T02:00:00Z"
TS3 = "2026-10-16T03:00:00Z"

DETAIL_150 = ("对 svc-shop 全谱测绘：端口指纹 8001-8008 逐服务 GET/HEAD/POST 探测，"
              "根路径行为分型 404/401/200，Server 头 BaseHTTP/0.6，"
              "DNS 解析 172.28.0.3，输出资产树与攻击面清单供后续意图复用。")
FACT_DETAIL_100 = ("svc-shop 8001 端口开放，GET / 返回 404 not found，"
                   "Server=BaseHTTP/0.6 Python/3.12.14，probe1 容器通道实测记录在案。")
FD_TITLE_LONG = ("反射 XSS 回显（/search?q=）svc-shop 检出面 GTXSS-01 "
                 "响应含脚本码形与漏洞语义文案 CWE-79 完整标题不截断验证样本" + "x" * 60)


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


def build_rich_ledger(td):
    """富卡夹具：覆盖七 kind×三态×截断边界×同 id 追加行（事件溯源）。"""
    gd = os.path.join(td, "G-g1")
    os.makedirs(gd)
    core.write_tsv(os.path.join(gd, "goals.tsv"), [row(
        "goals.tsv", id="G-g1-0001", target="authorized-range.local",
        objective="授权训练靶场完整渗透：8 服务端口异构，穷尽 HTTP 探测并出真实战绩",
        budget="1000;100;10", schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "intents.tsv"), [
        row("intents.tsv", id="INT-g1-0001", title="靶场全谱测绘", status="done",
            kind="recon", origin="entity", detail=DETAIL_150,
            schema_version="2", created=TS1),
        row("intents.tsv", id="INT-g1-0002", title="越权试探（AI 提议）",
            status="candidate", kind="authz-diff", origin="llm",
            schema_version="2", created=TS2),
        row("intents.tsv", id="INT-g1-0003", title="凭据复用面核查", status="pending",
            kind="cred-abuse", origin="entity", schema_version="2", created=TS2),
        # 事件溯源追加行：同 id 先 candidate 后 active（set-intent-status 整行复制）
        row("intents.tsv", id="INT-g1-0004", title="配置类实证（CORS 族）",
            status="candidate", kind="matrix-test", origin="entity",
            schema_version="2", created=TS2),
        row("intents.tsv", id="INT-g1-0004", title="配置类实证（CORS 族）",
            status="active", kind="matrix-test", origin="entity",
            schema_version="2", created=TS3),
    ])
    core.write_tsv(os.path.join(gd, "assets.tsv"), [
        row("assets.tsv", id="AST-g1-0001", type="service", value="svc-shop:8001",
            meta="root=404", in_scope="1", schema_version="2", created=TS1),
        row("assets.tsv", id="AST-g1-0002", type="service", value="svc-files:8008",
            meta="range 外发现", in_scope="out_of_scope",
            schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "creds.tsv"), [row(
        "creds.tsv", id="CRED-g1-0001", kind="static-cred", role="user",
        username_ref="admin", scope_asset="AST-g1-0001", status="active",
        schema_version="2", created=TS1)])
    core.write_tsv(os.path.join(gd, "facts.tsv"), [
        row("facts.tsv", id="F-g1-0001", intent_id="INT-g1-0001", kind="port",
            target="AST-g1-0001", detail=FACT_DETAIL_100, confidence="1.0",
            schema_version="2", created=TS1),
        row("facts.tsv", id="F-g1-0002", intent_id="INT-g1-0001", kind="port",
            target="AST-g1-0002", detail="", confidence="",
            schema_version="2", created=TS2)])
    core.write_tsv(os.path.join(gd, "findings.tsv"), [
        row("findings.tsv", id="FD-g1-0001", intent_id="INT-g1-0001",
            title=FD_TITLE_LONG, confidence="C1", impact="高",
            exploitation_status="verified", dedup_key="xss-reflect-search",
            vuln_ref="CWE-79", scope_check="in_scope", status="active",
            affected_asset_id="AST-g1-0001", schema_version="2", created=TS2),
        row("findings.tsv", id="FD-g1-0002", intent_id="INT-g1-0002",
            title="admin 面板匿名可读（疑似）", confidence="C2", impact="中",
            exploitation_status="suspected", dedup_key="admin-anon",
            status="open", affected_asset_id="AST-g1-0001",
            schema_version="2", created=TS2),
        # 事件溯源追加行：同 id 先 suspected 后 verified（最新行生效）
        row("findings.tsv", id="FD-g1-0003", intent_id="INT-g1-0003",
            title="CORS 通配放行", confidence="C1", impact="低",
            exploitation_status="suspected", dedup_key="cors-wild",
            status="open", schema_version="2", created=TS2),
        row("findings.tsv", id="FD-g1-0003", intent_id="INT-g1-0003",
            title="CORS 通配放行", confidence="C1", impact="低",
            exploitation_status="verified", dedup_key="cors-wild",
            status="active", schema_version="2", created=TS3)])
    core.write_tsv(os.path.join(gd, "E-index.tsv"), [
        row("E-index.tsv", id="EV-g1-0001", title="反射 XSS 回显（GTXSS-01）",
            source_type="command", observed_at=TS1, repro_kind="single",
            content_hash_raw="a" * 64, content_hash_norm="b" * 64,
            raw_excerpt="<html>probeX1</html>", schema_version="2", created=TS1),
        row("E-index.tsv", id="EV-g1-0002", title="CORS 响应头采样",
            source_type="http", observed_at=TS2, repro_kind="single",
            content_hash_raw="c" * 64, content_hash_norm="d" * 64,
            raw_excerpt="Access-Control-Allow-Origin: *",
            schema_version="2", created=TS2)])
    edge_rows = [
        ("spawns", "G-g1-0001", "INT-g1-0001"),
        ("yields", "INT-g1-0001", "F-g1-0001"),
        ("derived_from", "F-g1-0001", "INT-g1-0003"),
        ("proves", "INT-g1-0001", "FD-g1-0001"),
        ("parent", "AST-g1-0001", "AST-g1-0002"),
        ("attack", "FD-g1-0001", "AST-g1-0001"),
        ("cross_ref", "F-g1-0001", "FD-g1-0001"),
        ("evidences", "EV-g1-0001", "FD-g1-0001"),
        ("supersedes", "EV-g1-0002", "EV-g1-0001"),
        ("scope-rel", "AST-g1-0001", "AST-g1-0002"),
    ]
    core.write_tsv(os.path.join(gd, "edges.tsv"), [
        row("edges.tsv", id="E-g1-%04d" % (i + 1), kind=k, source_id=sr,
            target_id=ds, provenance="P2", schema_version="2", created=TS1)
        for i, (k, sr, ds) in enumerate(edge_rows)])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), chained_tl([
        (TS1, "总控", "P0", "add-goal G-g1-0001"),
        (TS2, "CLI", "P2", "replay-probe EV-g1-0001 verdict=reproduced"),
        (TS3, "总控", "P3", "add-fact F-g1-0001")]))
    return gd


def dir_bytes(gd):
    out = {}
    for n in sorted(os.listdir(gd)):
        p = os.path.join(gd, n)
        if os.path.isfile(p):
            with open(p, "rb") as f:
                out[n] = f.read()
    return out


class RichBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = build_rich_ledger(self.td.name)

    def _empty(self):
        empty = os.path.join(self.td.name, "G-empty")
        os.makedirs(empty)
        return empty


class TestCardFields(RichBase):
    """卡片字段齐：每节点 num/kind/badge/title/status/layer + 旧字段兼容。"""

    def test_every_node_carries_card_fields(self):
        gv = proj_mod.graph_view(self.gd)
        self.assertTrue(gv["nodes"])
        for n in gv["nodes"]:
            for f in ("id", "num", "kind", "badge", "title", "status",
                      "layer", "label", "candidate", "unverified"):
                self.assertIn(f, n, "%s 缺 %s" % (n.get("id"), f))

    def test_badge_chinese_names(self):
        gv = proj_mod.graph_view(self.gd)
        expect = {"G": "目标", "INT": "意图", "AST": "资产", "CRED": "凭据",
                  "F": "事实", "FD": "发现", "EV": "证据"}
        for n in gv["nodes"]:
            self.assertEqual(n["badge"], expect[n["kind"]], n["id"])

    def test_status_enum_only_three(self):
        gv = proj_mod.graph_view(self.gd)
        for n in gv["nodes"]:
            self.assertIn(n["status"], ("进行中", "已完成", "未证实"), n["id"])


class TestNum(RichBase):
    """编号：全图唯一短编号，按类型计数（T1/I3/F12/V7 式）。"""

    def test_num_globally_unique(self):
        nums = [n["num"] for n in proj_mod.graph_view(self.gd)["nodes"]]
        self.assertEqual(len(nums), len(set(nums)), "编号须全图唯一")

    def test_num_format_and_prefix(self):
        prefix = {"G": "T", "INT": "I", "AST": "A", "CRED": "C",
                  "F": "F", "FD": "V", "EV": "E"}
        gv = proj_mod.graph_view(self.gd)
        for n in gv["nodes"]:
            self.assertRegex(n["num"], r"^[A-Z][0-9]+$", n["id"])
            self.assertEqual(n["num"][0], prefix[n["kind"]], n["id"])

    def test_num_counts_by_kind_in_id_order(self):
        gv = proj_mod.graph_view(self.gd)
        by_kind = {}
        for n in gv["nodes"]:
            by_kind.setdefault(n["kind"], []).append(n["num"])
        self.assertEqual(by_kind["G"], ["T1"])
        self.assertEqual(by_kind["INT"], ["I1", "I2", "I3", "I4"])  # 同 id 去重
        self.assertEqual(by_kind["AST"], ["A1", "A2"])
        self.assertEqual(by_kind["CRED"], ["C1"])
        self.assertEqual(by_kind["F"], ["F1", "F2"])
        self.assertEqual(by_kind["FD"], ["V1", "V2", "V3"])          # 同 id 去重
        self.assertEqual(by_kind["EV"], ["E1", "E2"])


class TestTitle(RichBase):
    """title 规则：意图=目的原文前120字/发现=完整标题/事实=摘要前80字/其余=id+简述。"""

    def test_intent_title_purpose_first_120(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["INT-g1-0001"]["title"], DETAIL_150[:120])
        self.assertTrue(by_id["INT-g1-0001"]["title"].startswith(DETAIL_150[:20]))

    def test_intent_title_fallback_when_detail_empty(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["INT-g1-0002"]["title"], "越权试探（AI 提议）")

    def test_finding_title_full_never_truncated(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["FD-g1-0001"]["title"], FD_TITLE_LONG)
        self.assertGreater(len(FD_TITLE_LONG), 120)   # 夹具保证超长仍全文

    def test_fact_title_summary_first_80(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["F-g1-0001"]["title"], FACT_DETAIL_100[:80])

    def test_other_kinds_id_plus_brief(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        g = by_id["G-g1-0001"]["title"]
        self.assertTrue(g.startswith("G-g1-0001"), g)
        self.assertIn("授权训练靶场完整渗透", g)                      # objective 简述
        a = by_id["AST-g1-0001"]["title"]
        self.assertTrue(a.startswith("AST-g1-0001"), a)
        self.assertIn("svc-shop:8001", a)                            # value 简述
        c = by_id["CRED-g1-0001"]["title"]
        self.assertTrue(c.startswith("CRED-g1-0001"), c)
        self.assertIn("admin", c)                                    # username 简述
        e = by_id["EV-g1-0001"]["title"]
        self.assertTrue(e.startswith("EV-g1-0001"), e)
        self.assertIn("反射 XSS 回显（GTXSS-01）", e)                # E-index title 简述

    def test_title_nonempty_rate(self):
        nodes = proj_mod.graph_view(self.gd)["nodes"]
        self.assertGreater(
            sum(1 for n in nodes if n["title"].strip()) / len(nodes), 0.9)
        for kind in ("INT", "FD"):
            sub = [n for n in nodes if n["kind"] == kind]
            self.assertTrue(sub)
            rate = sum(1 for n in sub if n["title"].strip()) / len(sub)
            self.assertGreaterEqual(rate, 0.9, kind + " title 非空率须>90%")


class TestStatus(RichBase):
    """status 三态：意图状态机/发现实证态/证据重放态/资产范围/凭据活性。"""

    def test_intent_status_machine(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["INT-g1-0001"]["status"], "已完成")     # done
        self.assertEqual(by_id["INT-g1-0002"]["status"], "未证实")     # candidate
        self.assertEqual(by_id["INT-g1-0003"]["status"], "进行中")     # pending
        self.assertEqual(by_id["INT-g1-0004"]["status"], "进行中")     # latest=active

    def test_finding_status(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["FD-g1-0001"]["status"], "已完成")      # verified
        self.assertEqual(by_id["FD-g1-0002"]["status"], "未证实")      # suspected
        self.assertEqual(by_id["FD-g1-0003"]["status"], "已完成")      # latest=verified

    def test_fact_asset_cred_evidence_status(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["F-g1-0001"]["status"], "已完成")       # confidence 在册
        self.assertEqual(by_id["F-g1-0002"]["status"], "未证实")       # confidence 空
        self.assertEqual(by_id["AST-g1-0001"]["status"], "已完成")     # in_scope
        self.assertEqual(by_id["AST-g1-0002"]["status"], "未证实")     # out_of_scope
        self.assertEqual(by_id["CRED-g1-0001"]["status"], "进行中")    # active
        self.assertEqual(by_id["EV-g1-0001"]["status"], "已完成")      # verdict reproduced
        self.assertEqual(by_id["EV-g1-0002"]["status"], "未证实")      # 未重放

    def test_unverified_dim_marker(self):
        gv = proj_mod.graph_view(self.gd)
        for n in gv["nodes"]:
            self.assertEqual(n["unverified"], n["status"] == "未证实", n["id"])
        by_id = {n["id"]: n for n in gv["nodes"]}
        self.assertTrue(by_id["INT-g1-0002"]["candidate"])          # 旧淡显语义保留
        self.assertTrue(by_id["INT-g1-0002"]["unverified"])
        self.assertFalse(by_id["INT-g1-0001"]["unverified"])


class TestImpact(RichBase):
    """impact 仅发现节点携带，值=findings.impact 原文。"""

    def test_impact_only_on_findings(self):
        gv = proj_mod.graph_view(self.gd)
        for n in gv["nodes"]:
            if n["kind"] == "FD":
                self.assertIn("impact", n, n["id"])
                self.assertTrue(n["impact"].strip(), n["id"])
            else:
                self.assertNotIn("impact", n, n["id"] + " 仅发现才有 impact")

    def test_impact_values(self):
        by_id = {n["id"]: n for n in proj_mod.graph_view(self.gd)["nodes"]}
        self.assertEqual(by_id["FD-g1-0001"]["impact"], "高")
        self.assertEqual(by_id["FD-g1-0002"]["impact"], "中")


class TestEdgesKept(RichBase):
    """边保持现 10 型+标签：形状不变，新增 label=kind 供画布段常显。"""

    def test_edges_ten_kinds_with_label(self):
        gv = proj_mod.graph_view(self.gd)
        self.assertEqual({e["kind"] for e in gv["edges"]}, EDGE_KINDS)
        for e in gv["edges"]:
            for f in ("id", "kind", "src", "dst"):
                self.assertIn(f, e)
            self.assertEqual(e["label"], e["kind"])

    def test_edge_style_unchanged(self):
        es = proj_mod.graph_view(self.gd)["edge_style"]
        self.assertEqual(set(es), EDGE_KINDS)
        self.assertEqual(len({(v["color"], v["dash"]) for v in es.values()}), 10)


class TestEventSourcing(RichBase):
    """事件溯源：同 id 追加行 latest-wins——节点数=唯一 id 数，字段取最新行。"""

    def test_no_duplicate_nodes_for_appended_rows(self):
        gv = proj_mod.graph_view(self.gd)
        ids = [n["id"] for n in gv["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 15)          # 1G+4INT+2AST+1CRED+2F+3FD+2EV 唯一 id
        self.assertEqual(gv["stats"]["nodes"], 15)
        self.assertEqual(gv["stats"]["edges"], 10)


class TestProjectStyle(RichBase):
    """投影律：只读零写入/确定性/JSON 可序列化/空目录容错。"""

    def test_readonly(self):
        before = dir_bytes(self.gd)
        proj_mod.graph_view(self.gd)
        self.assertEqual(dir_bytes(self.gd), before)

    def test_deterministic_and_json_serializable(self):
        a, b = proj_mod.graph_view(self.gd), proj_mod.graph_view(self.gd)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_empty_dir_tolerant(self):
        gv = proj_mod.graph_view(self._empty())
        self.assertEqual(gv["nodes"], [])
        self.assertEqual(gv["edges"], [])
        self.assertEqual(gv["stats"]["nodes"], 0)
        self.assertEqual(gv["stats"]["edges"], 0)


if __name__ == "__main__":
    unittest.main()
