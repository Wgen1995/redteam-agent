# -*- coding: utf-8 -*-
"""W3 工具卡（蓝图 W3·B52）：cli/tools 新模块——25 卡注册表/纪律字段/执行入口
（必过现有执法层：deny-list+scope 经 tanyin-guard 委托、L3 审批门挂卡）/
卡片清单命令/tools.lock 供应链锁定（版本+sha256+ECDSA 验签）。

测试钥锚（批次 4 先例：TEST-ONLY 测试钥签名，生产钥离线重签仪式=
install/KEY-MANAGEMENT.md）：tests/fixtures/keys/test-signing-key.pem。
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
sys.path.insert(0, CLI)

from tools import cards as tool_cards  # noqa: E402
from tools import lock as tool_lock  # noqa: E402
from tools import install as tool_install  # noqa: E402

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


class TestDisciplineCompleteness(unittest.TestCase):
    """每卡纪律字段完整性：七字段显式齐备、值域合法、示例=binary 打头。"""

    def test_every_card_passes_discipline_check(self):
        bad = {}
        for c in tool_cards.all_cards():
            errs = c.discipline_errors()
            if errs:
                bad[c.name] = errs
        self.assertEqual(bad, {}, "纪律字段不备的卡: %s" % bad)

    def test_every_card_has_seven_discipline_fields_nonempty(self):
        for c in tool_cards.all_cards():
            for field in ("name", "tier", "rate", "revert", "risk"):
                self.assertTrue(getattr(c, field), "%s.%s 空" % (c.name, field))
            self.assertIsNotNone(c.deny_extra, "%s.deny_extra 未声明" % c.name)
            self.assertTrue(c.example, "%s.example 空" % c.name)

    def test_tier_and_risk_in_enum(self):
        for c in tool_cards.all_cards():
            self.assertIn(c.tier, tool_cards.TIERS, c.name)
            self.assertIn(c.risk, tool_cards.RISKS, c.name)

    def test_rate_syntax_valid(self):
        for c in tool_cards.all_cards():
            self.assertRegex(c.rate, tool_cards.RATE_RE.pattern,
                             "%s.rate 形非法: %r" % (c.name, c.rate))

    def test_example_command_starts_with_binary(self):
        for c in tool_cards.all_cards():
            self.assertEqual(c.example[0], c.binary, c.name)

    def test_l3_cards_exactly_sqlmap_and_impacket(self):
        l3 = sorted(c.name for c in tool_cards.all_cards() if c.tier == "L3")
        self.assertEqual(l3, ["impacket", "sqlmap"],
                         "L3 档（审批门挂卡面）必须恰为 sqlmap+impacket")

    def test_l3_cards_require_approval_flag(self):
        for c in tool_cards.all_cards():
            self.assertEqual(c.requires_approval, c.tier == "L3", c.name)

    def test_readonly_revert_declared_explicitly(self):
        """只读卡 revert=none(只读) 显式声明；非只读=核销义务文案（has_obligation 真）。"""
        for c in tool_cards.all_cards():
            if c.revert == tool_cards.READONLY_REVERT:
                self.assertFalse(c.has_revert_obligation, c.name)
            else:
                self.assertTrue(c.has_revert_obligation, c.name)

    def test_register_incomplete_card_rejected(self):
        bad = tool_cards.ToolCard(
            name="w3-bad", binary="", tier="L9", rate="", deny_extra=None,
            revert="", example=[], risk="extreme", category="", summary="")
        errs = bad.discipline_errors()
        for frag in ("binary", "tier", "rate", "deny_extra", "revert",
                     "example", "risk", "category", "summary"):
            self.assertTrue(any(frag in e for e in errs),
                            "缺字段 %s 未被 discipline_errors 报出" % frag)
        with self.assertRaises(tool_cards.CardError):
            tool_cards.register(bad)


class TestToolsLock(unittest.TestCase):
    """④tools.lock 供应链锁定（版本+sha256+ECDSA 验签；测试钥锚=批次 4 先例）。"""

    def test_lock_file_covers_all_25_cards(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        self.assertEqual(sorted(entries), sorted(REQUIRED_25),
                         "lock 键面=注册表 25 卡全量")

    def test_lock_all_entries_signature_verifies(self):
        results = tool_lock.verify_all(tool_lock.DEFAULT_LOCK_PATH, TEST_PUB)
        bad = [(n, why) for n, ok, why in results if not ok]
        self.assertEqual(bad, [], "验签不过: %s" % bad)

    def test_lock_entries_match_registry_digest(self):
        for name in REQUIRED_25:
            ok, why = tool_lock.verify_card(tool_cards.get_card(name),
                                            tool_lock.DEFAULT_LOCK_PATH, TEST_PUB)
            self.assertTrue(ok, "%s 卡内容与 lock 锚不符: %s" % (name, why))

    def test_tampered_sha256_rejected(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        entries["nuclei"]["sha256"] = "ab" * 32
        ok, why = tool_lock._verify_entry("nuclei", entries["nuclei"], TEST_PUB)
        self.assertFalse(ok, "篡改 sha256 必须验签失败: " + why)

    def test_tampered_sig_rejected(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        entries["nmap"]["sig"] = "00" * 32
        ok, why = tool_lock._verify_entry("nmap", entries["nmap"], TEST_PUB)
        self.assertFalse(ok, "篡改 sig 必须失败: " + why)

    def test_nonhex_sig_fail_closed(self):
        ok, why = tool_lock._verify_entry(
            "dig", {"version": "w3-1", "sha256": "cd" * 32, "sig": "XYZ"}, TEST_PUB)
        self.assertFalse(ok, "非 hex sig=fail-closed: " + why)

    def test_missing_entry_fails_card_verify(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        del entries["curl"]
        tmp = os.path.join(tempfile.mkdtemp(), "tools.lock")
        tool_lock.write_entries(tmp, entries)
        self.addCleanup(shutil.rmtree, os.path.dirname(tmp))
        ok, why = tool_lock.verify_card(tool_cards.get_card("curl"), tmp, TEST_PUB)
        self.assertFalse(ok, "缺条目必须失败: " + why)

    def test_card_content_drift_detected(self):
        """红队反例：注册表卡内容被改（如限速放松）——sha256 与 lock 锚不符必拒。"""
        c = tool_cards.get_card("ffuf")
        orig = c.rate
        c.rate = "9999/s"
        try:
            ok, why = tool_lock.verify_card(c, tool_lock.DEFAULT_LOCK_PATH, TEST_PUB)
            self.assertFalse(ok, "卡内容漂移必须检出: " + why)
            self.assertIn("sha256", why)
        finally:
            c.rate = orig

    def test_sign_verify_roundtrip_with_test_key(self):
        c = tool_cards.ToolCard(
            name="w3-sign-probe", binary="w3-sign-probe", tier="L0",
            rate="local", deny_extra=[], revert="none(只读)",
            example=["w3-sign-probe", "--version"], risk="low",
            category="recon", summary="签名往返探针", version="rt-1")
        sig = tool_lock.sign_card(c, TEST_KEY)
        entry = {"version": c.version, "sha256": tool_lock.card_digest(c),
                 "sig": sig}
        ok, why = tool_lock._verify_entry(c.name, entry, TEST_PUB)
        self.assertTrue(ok, why)

    def test_lock_file_lf_no_bom(self):
        raw = open(tool_lock.DEFAULT_LOCK_PATH, "rb").read()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "BOM 禁入")
        self.assertNotIn(b"\r\n", raw, "CRLF 禁入（selfcheck encoding 律）")


class TestInstallCard(unittest.TestCase):
    """③装卡验签：验签不过不装、在役清单 sha 鲜度、幂等重装。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.state = os.path.join(self.td.name, "installed.tsv")

    def test_install_writes_state_and_is_installed(self):
        ok, why = tool_install.install("nuclei", "2026-10-18T10:00:00Z",
                                       state_path=self.state)
        self.assertTrue(ok, why)
        self.assertTrue(tool_install.is_installed(
            tool_cards.get_card("nuclei"), state_path=self.state))

    def test_not_installed_before_install(self):
        self.assertFalse(tool_install.is_installed(
            tool_cards.get_card("nuclei"), state_path=self.state))

    def test_install_idempotent_same_digest(self):
        tool_install.install("dig", "2026-10-18T10:00:00Z", state_path=self.state)
        ok, why = tool_install.install("dig", "2026-10-18T11:00:00Z",
                                       state_path=self.state)
        self.assertTrue(ok, why)
        rows = tool_install.load_state(self.state)
        self.assertEqual(len([r for r in rows if r["name"] == "dig"]), 1,
                         "同摘要重装=幂等不重复入册")

    def test_install_unknown_card_rejected(self):
        ok, why = tool_install.install("metasploit", "2026-10-18T10:00:00Z",
                                       state_path=self.state)
        self.assertFalse(ok)
        self.assertIn("unknown-tool", why)

    def test_install_tampered_lock_refused(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        entries["nikto"]["sha256"] = "ab" * 32
        tmp_lock = os.path.join(self.td.name, "tools.lock")
        tool_lock.write_entries(tmp_lock, entries)
        ok, why = tool_install.install("nikto", "2026-10-18T10:00:00Z",
                                       state_path=self.state,
                                       lock_path=tmp_lock)
        self.assertFalse(ok, "篡改 lock 不得装卡: " + why)
        self.assertFalse(tool_install.is_installed(
            tool_cards.get_card("nikto"), state_path=self.state))

    def test_stale_install_after_card_drift(self):
        tool_install.install("ffuf", "2026-10-18T10:00:00Z", state_path=self.state)
        c = tool_cards.get_card("ffuf")
        orig = c.rate
        c.rate = "9999/s"
        try:
            self.assertFalse(tool_install.is_installed(
                c, state_path=self.state), "卡漂移后在役行过期（sha 不符）")
        finally:
            c.rate = orig
        self.assertTrue(tool_install.is_installed(
            c, state_path=self.state), "复原后在役行重新有效")

    def test_uninstall_removes_roster_row(self):
        tool_install.install("curl", "2026-10-18T10:00:00Z", state_path=self.state)
        tool_install.uninstall("curl", state_path=self.state)
        self.assertFalse(tool_install.is_installed(
            tool_cards.get_card("curl"), state_path=self.state))

    def test_state_lf_no_crlf(self):
        tool_install.install("openssl", "2026-10-18T10:00:00Z",
                             state_path=self.state)
        raw = open(self.state, "rb").read()
        self.assertNotIn(b"\r\n", raw)


if __name__ == "__main__":
    unittest.main()
