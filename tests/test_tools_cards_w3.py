# -*- coding: utf-8 -*-
"""W3 工具卡（蓝图 W3·B52）：cli/tools 新模块——25 卡注册表/纪律字段/执行入口
（必过现有执法层：deny-list+scope 经 tanyin-guard 委托、L3 审批门挂卡）/
卡片清单命令/tools.lock 供应链锁定（版本+sha256+ECDSA 验签）。

测试钥锚（批次 4 先例：TEST-ONLY 测试钥签名，生产钥离线重签仪式=
install/KEY-MANAGEMENT.md）：tests/fixtures/keys/test-signing-key.pem。
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
sys.path.insert(0, CLI)

from tools import cards as tool_cards  # noqa: E402

TEST_KEY = os.path.join(HERE, "fixtures", "keys", "test-signing-key.pem")
TEST_PUB = os.path.join(HERE, "fixtures", "keys", "test-release.pub")
FIXTURE = os.path.join(HERE, "fixtures", "G-g1")

# 蓝图 W3 工具卡 25 张（名称冻结清单——增删卡须改本表+tools.lock 重签）
REQUIRED_25 = (
    "nuclei", "nmap", "sqlmap", "httpx", "subfinder", "katana", "ffuf",
    "curl", "dig", "testssl", "wafw00f", "whatweb", "gobuster", "nikto",
    "redis-cli", "mysql-client", "kubectl", "impacket", "kerberoast",
    "bloodhound", "smbclient", "ldapsearch", "dnsrecon", "theHarvester",
    "openssl",
)


class TestRegistry25Cards(unittest.TestCase):
    """①卡片注册表：25 张全注册、名称无重复、按名可查、未注册查 None。"""

    def test_registry_has_exactly_25_cards(self):
        self.assertEqual(len(tool_cards.all_cards()), 25,
                         "注册表必须恰 25 张（蓝图 W3 工具卡 25 张口径）")

    def test_required_names_all_registered(self):
        missing = [n for n in REQUIRED_25 if tool_cards.get_card(n) is None]
        self.assertEqual(missing, [], "蓝图 25 卡缺注册: %s" % missing)

    def test_registry_names_unique(self):
        names = [c.name for c in tool_cards.all_cards()]
        self.assertEqual(len(names), len(set(names)), "卡名必须唯一")

    def test_get_card_unknown_returns_none(self):
        self.assertIsNone(tool_cards.get_card("metasploit"))
        self.assertIsNone(tool_cards.get_card(""))

    def test_register_duplicate_name_rejected(self):
        dup = tool_cards.get_card("nuclei")
        with self.assertRaises(tool_cards.CardError):
            tool_cards.register(dup)

    def test_register_new_card_ok_and_removable(self):
        extra = tool_cards.ToolCard(
            name="w3-tmp-probe", binary="w3-tmp-probe", tier="L0",
            rate="local", deny_extra=[], revert="none(只读)",
            example=["w3-tmp-probe", "--version"], risk="low",
            category="recon", summary="临时测试卡")
        tool_cards.register(extra)
        try:
            self.assertIs(tool_cards.get_card("w3-tmp-probe"), extra)
        finally:
            tool_cards.unregister("w3-tmp-probe")
        self.assertIsNone(tool_cards.get_card("w3-tmp-probe"))


if __name__ == "__main__":
    unittest.main()
