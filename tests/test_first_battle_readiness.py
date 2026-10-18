# -*- coding: utf-8 -*-
"""首场真仗免费前置钉——DEMO-1 演示战役 + 真模型道样例(脱敏)两工件就位。

宪法#43 第一性=找漏洞效果: 首仗前置工件为"点火即打"服务——
演示战役要过验链(演示不用假账), 道样例要能被战士入口真加载且真钥零回流(文案#41 人话标注)。

红→绿: 工件未建时本套红; 建 demos/DEMO-1(拷自 tests/fixtures/G-r18)与
cli/warrior/channels.example.json(真钥脱敏样例)后转绿。

python3 -m unittest tests.test_first_battle_readiness
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
sys.path.insert(0, CLI)
sys.path.insert(0, ROOT)

EXAMPLE = os.path.join(CLI, "warrior", "channels.example.json")
DEMO = os.path.join(ROOT, "demos", "DEMO-1")
SRC_FIXTURE = os.path.join(HERE, "fixtures", "G-r18")

# 真钥形状黑名单(防脱敏漏网回流): sk- 前缀 / bigmodel「id.secret」形 / 长十六进制串
_REAL_KEY_SHAPES = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"[A-Za-z0-9]{24,}\.[A-Za-z0-9]{8,}"),
    re.compile(r"[A-Fa-f0-9]{32,}"),
)
PLACEHOLDER = "YOUR_API_KEY"


class ChannelsExampleShapeTest(unittest.TestCase):
    """channels.example.json: 战士 --channels 真消费面可加载 + 真钥零回流。"""

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(EXAMPLE),
                        "缺 cli/warrior/channels.example.json")

    def test_valid_channel_list_with_required_fields(self):
        with open(EXAMPLE, encoding="utf-8") as f:
            doc = json.load(f)
        self.assertIsInstance(doc, list)
        self.assertGreaterEqual(len(doc), 1)
        for c in doc:
            self.assertIsInstance(c, dict)
            for k in ("name", "model", "base_url", "api_key"):
                self.assertTrue(c.get(k),
                                "通道 %r 缺字段 %s" % (c.get("name"), k))

    def test_keys_are_placeholders_not_real_secrets(self):
        with open(EXAMPLE, encoding="utf-8") as f:
            raw = f.read()
        doc = json.loads(raw)
        for c in doc:
            self.assertIn(PLACEHOLDER, c["api_key"],
                          "api_key 未用占位符: %r" % c.get("name"))
        for pat in _REAL_KEY_SHAPES:
            self.assertIsNone(pat.search(raw),
                              "样例文件检出真钥形状: %s" % pat.pattern)

    def test_warrior_loader_accepts_example(self):
        from warrior.__main__ import _load_channels
        channels = _load_channels(EXAMPLE)  # 拒收=SystemExit(2) 测试即红
        self.assertGreaterEqual(len(channels), 1)


class DemoCampaignTest(unittest.TestCase):
    """demos/DEMO-1: G-r18 拷贝完整 + 标注演示 + 验链 PASS。"""

    def test_dir_exists_as_copy_of_g_r18(self):
        for tsv in ("timeline.tsv", "findings.tsv", "E-index.tsv", "goals.tsv"):
            src = os.path.join(SRC_FIXTURE, tsv)
            dst = os.path.join(DEMO, tsv)
            self.assertTrue(os.path.isfile(dst), "DEMO-1 缺 %s" % tsv)
            with open(src, "rb") as a, open(dst, "rb") as b:
                self.assertEqual(a.read(), b.read(),
                                 "DEMO-1/%s 与源夹具不一致" % tsv)

    def test_demo_marker_file(self):
        marker = os.path.join(DEMO, "DEMO-README.md")
        self.assertTrue(os.path.isfile(marker), "缺演示标注 DEMO-README.md")
        with open(marker, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("演示", text)
        self.assertIn("G-r18", text)

    def test_verify_chain_passes_with_full_ledger(self):
        from ledger.core import Session
        s = Session(DEMO)
        ok, bad = s.verify_chain()
        self.assertTrue(ok, "DEMO-1 链断行=%s" % bad)
        self.assertEqual(s.gate_jump_errors(), [])
        self.assertEqual(len(s.rows("timeline.tsv")), 709)
        self.assertEqual(len(s.rows("findings.tsv")), 111)


if __name__ == "__main__":
    unittest.main()
