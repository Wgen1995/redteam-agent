# -*- coding: utf-8 -*-
"""W4 白盒·锚边契约测试: contracts/01-ledger-schema.md 第 11 边型 anchor。

依据: docs/design/source-audit-v1.md §1.2「锚」行——
  edges.tsv 第 11 边型 anchor（方向阵 {facts,intents,findings}→assets,归 asset 类,
  provenance 必填 file:line+工件 sha256——比 ARTEX 裸两列桥强,F1-2 裁决继承,
  走 schema bump+微版本勘误,W4 已在册）。
施工口径（本舰任务令）: schema bump 走微版本勘误,照 schema 里既有 bump 先例
（G-12 十一值枚举/priority/cred 落列同通道: 零存量数据期,schema_version 保持=2 不递增）。
write_cmds.py 的 EDGE_KINDS 执法面由并行舰落（本舰禁碰）——本测试只钉契约文档。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCHEMA = os.path.join(ROOT, "contracts", "01-ledger-schema.md")
README = os.path.join(ROOT, "contracts", "README.md")


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _edge_vocab_section(doc):
    m = re.search(r"^## 4 .*?^## ", doc, re.S | re.M)
    return m.group(0) if m else ""


def _edge_rows(doc):
    rows = []
    for line in _edge_vocab_section(doc).splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([a-z_-]+)\s*\|([^|]*)\|(.*)$", line)
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3), m.group(4)))
    return rows


class TestAnchorEdgeContract(unittest.TestCase):
    def test_edge_vocab_has_11th_edge_anchor(self):
        rows = _edge_rows(_read(SCHEMA))
        self.assertEqual(len(rows), 11, "边词汇表应为 11 行(10+anchor 勘误)")
        self.assertEqual([r[0] for r in rows], list(range(1, 12)))
        num, kind, direction, semantics = rows[-1]
        self.assertEqual(kind, "anchor")

    def test_anchor_direction_is_process_domain_to_assets(self):
        _, _, direction, _ = _edge_rows(_read(SCHEMA))[-1]
        for tok in ("facts", "intents", "findings"):
            self.assertIn(tok, direction)
        self.assertIn("assets", direction)
        self.assertIn("→", direction, "方向记号必须显式(防无向边歧义)")

    def test_anchor_provenance_requires_file_line_and_artifact_sha(self):
        _, _, _, semantics = _edge_rows(_read(SCHEMA))[-1]
        self.assertIn("file:line", semantics)
        self.assertIn("sha256", semantics)

    def test_edges_table_enum_mentions_11(self):
        doc = _read(SCHEMA)
        m = re.search(r"### 3\.7 edges\.tsv.*?\|\s*kind\s*\|[^\n]*", doc, re.S)
        self.assertTrue(m, "§3.7 edges 表 kind 行应在")
        self.assertIn("11 边", m.group(0))

    def test_micro_version_errata_precedent_followed(self):
        doc = _read(SCHEMA)
        sections = doc.split("\n## ")
        anchor_sects = [s for s in sections
                        if s.startswith("v2 勘误补记") and "anchor" in s]
        self.assertTrue(anchor_sects, "应存在 anchor 勘误补记节")
        body = anchor_sects[0][:3000]
        self.assertIn("微版本", body)
        self.assertIn("不递增", body)
        self.assertIn("F1-2", body, "须引用 06-whitebox F1-2 裁决继承")

    def test_schema_version_stays_2(self):
        head = _read(SCHEMA)[:2000]
        self.assertIn("schema_version=2", head, "微版本勘误不升 schema_version(先例)")

    def test_readme_index_updated(self):
        body = _read(README)
        self.assertRegex(body, r"边词汇\s*10→\*\*11\*\*|10→\*\*11\*\*")


if __name__ == "__main__":
    unittest.main()
