# -*- coding: utf-8 -*-
"""W3 工具卡（蓝图 W3·B52）：cli/tools 新模块——25 卡注册表/纪律字段/执行入口
（必过现有执法层：deny-list+scope 经 tanyin-guard 委托、L3 审批门挂卡）/
卡片清单命令/tools.lock 供应链锁定（版本+sha256+ECDSA 验签）。

测试钥锚（批次 4 先例：TEST-ONLY 测试钥签名，生产钥离线重签仪式=
install/KEY-MANAGEMENT.md）：tests/fixtures/keys/test-signing-key.pem。
"""
import os
import shutil
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
sys.path.insert(0, CLI)

from tools import cards as tool_cards  # noqa: E402
from tools import lock as tool_lock  # noqa: E402
from tools import install as tool_install  # noqa: E402
from tools import gate as tool_gate  # noqa: E402

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
        """只读卡 revert=none(只读*) 家族显式声明；非只读=核销义务文案。"""
        for c in tool_cards.all_cards():
            if c.revert.startswith(tool_cards.READONLY_PREFIX):
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


LEDGER_ENTRY = os.path.join(ROOT, "cli", "tanyin-ledger")
PY = sys.executable


def _ledger(gd, *args):
    return subprocess.run([PY, LEDGER_ENTRY, args[0], "--goal-dir", gd]
                          + list(args[1:]), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestCardGate(unittest.TestCase):
    """②执行入口卡层门链：未注册拒/供应链门/黑名单覆盖/限速旗标/L3 审批挂卡。

    四层 scope 与全局 deny-list 在委托层（tanyin-guard exec 同源执法）——
    卡层不做第二份解释（防漂移），本组测卡层自有门；guard 委托面=集成组。
    """

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIXTURE, os.path.join(self.td.name, "G-g1"))
        self.state = os.path.join(self.td.name, "installed.tsv")
        for n in ("curl", "nuclei", "ffuf", "nmap", "sqlmap", "impacket",
                  "redis-cli", "dig"):
            ok, why = tool_install.install(n, "2026-10-18T10:00:00Z",
                                           state_path=self.state)
            assert ok, why

    def gate(self, name, args, ts="2026-10-18T12:00:00Z"):
        return tool_gate.card_gate(self.gd, name, args, ts,
                                   state_path=self.state)

    def test_unknown_card_rejected(self):
        ok, why = self.gate("metasploit", ["-h"])
        self.assertFalse(ok)
        self.assertIn("unknown-tool", why)

    def test_empty_card_name_rejected(self):
        ok, why = self.gate("", [])
        self.assertFalse(ok)
        self.assertIn("unknown-tool", why)

    def test_not_installed_card_rejected(self):
        ok, why = self.gate("nikto", ["-h", "https://api.shop.example"])
        self.assertFalse(ok)
        self.assertIn("card-not-installed", why)

    def test_tampered_lock_rejected_at_exec(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        entries["dig"]["sha256"] = "ab" * 32
        bad_lock = os.path.join(self.td.name, "tools-bad.lock")
        tool_lock.write_entries(bad_lock, entries)
        ok, why = tool_gate.card_gate(
            self.gd, "dig", ["+short", "A", "api.shop.example"],
            "2026-10-18T12:00:00Z", state_path=self.state,
            lock_path=bad_lock)
        self.assertFalse(ok, "执行时 lock 现场复验不过必须拒: " + why)
        self.assertIn("supply-chain", why)

    def test_deny_extra_pattern_rejected(self):
        ok, why = self.gate("redis-cli", ["-h", "db.shop.example", "FLUSHALL"])
        self.assertFalse(ok)
        self.assertIn("deny-extra", why)
        self.assertIn("FLUSHALL", why)

    def test_nmap_t5_aggressive_rejected(self):
        ok, why = self.gate("nmap", ["-T5", "-p", "443", "api.shop.example"])
        self.assertFalse(ok)
        self.assertIn("deny-extra", why)

    def test_sqlmap_max_risk_rejected(self):
        ok, why = self.gate("sqlmap", ["-u", "https://api.shop.example/?id=1",
                                       "--batch", "--risk=3"])
        self.assertFalse(ok)
        self.assertIn("deny-extra", why)

    def test_nuclei_missing_rate_flag_rejected(self):
        ok, why = self.gate("nuclei", ["-u", "https://api.shop.example"])
        self.assertFalse(ok)
        self.assertIn("card-rate", why)
        self.assertIn("-rl", why)

    def test_ffuf_missing_rate_flag_rejected(self):
        ok, why = self.gate("ffuf", ["-w", "w.txt",
                                     "-u", "https://api.shop.example/FUZZ"])
        self.assertFalse(ok)
        self.assertIn("card-rate", why)

    def test_nuclei_with_rate_flag_passes_card_layer(self):
        ok, why = self.gate("nuclei", ["-rl", "10", "-etags", "dos,intrusive",
                                       "-u", "https://api.shop.example"])
        self.assertTrue(ok, why)

    def test_l3_without_approval_rejected(self):
        ok, why = self.gate("sqlmap", ["-u", "https://api.shop.example/?id=1",
                                       "--batch", "--delay=1",
                                       "--risk=1", "--level=1"])
        self.assertFalse(ok)
        self.assertIn("approval-required", why)

    def test_l3_impacket_without_approval_rejected(self):
        ok, why = self.gate("impacket", ["dc.shop.example/user:x"])
        self.assertFalse(ok)
        self.assertIn("approval-required", why)

    def _approve_hash(self, argv):
        chash = tool_gate.command_hash(argv)
        r = _ledger(self.gd, "approve",
                    "--command-hash=" + chash, "--decision=approved",
                    "--approver=client-cso", "--timestamp=2026-10-18T11:00:00Z",
                    "--note=W3 L3 卡人审")
        assert r.returncode == 0, r.stdout + r.stderr
        return chash

    def test_l3_with_approved_hash_passes(self):
        argv = ["sqlmap", "-u", "https://api.shop.example/?id=1", "--batch",
                "--delay=1", "--risk=1", "--level=1"]
        self._approve_hash(argv)
        ok, why = self.gate("sqlmap", argv[1:])
        self.assertTrue(ok, why)

    def test_l3_approval_bound_to_exact_command(self):
        """审批绑定 command_hash：换一个参数（不同命令）≠ 已批命令，仍拒。"""
        argv = ["sqlmap", "-u", "https://api.shop.example/?id=2", "--batch",
                "--delay=1", "--risk=1", "--level=1"]
        self._approve_hash(argv)
        other = ["sqlmap", "-u", "https://api.shop.example/?id=999", "--batch",
                 "--delay=1", "--risk=1", "--level=1"]
        ok, why = self.gate("sqlmap", other[1:])
        self.assertFalse(ok)
        self.assertIn("approval-required", why)

    def test_non_l3_needs_no_approval(self):
        ok, why = self.gate("curl", ["-sS", "--max-time", "10",
                                     "https://api.shop.example/"])
        self.assertTrue(ok, why)

    def test_fixture_legacy_approval_not_honored_for_other_cmds(self):
        """夹具遗留 approved 行（bbbb..）不得放行任意 L3 命令——哈希逐字对照。"""
        ok, why = self.gate("sqlmap", ["-u", "https://api.shop.example/?id=1",
                                       "--batch"])
        self.assertFalse(ok)
        self.assertIn("approval-required", why)


GUARD_ENTRY = os.path.normpath(os.path.join(ROOT, "cli", "tanyin-guard"))


class FakeSpawn:
    """记录委托 argv 的假执行器（不触网不落地——execute 委托面单测）。"""

    def __init__(self, rc=0, out="", err=""):
        self.calls = []
        self.rc, self.out, self.err = rc, out, err

    def __call__(self, argv):
        self.calls.append(list(argv))
        return self.rc, self.out, self.err


class TestExecuteDelegation(unittest.TestCase):
    """②执行入口委托面：卡层门过 → tanyin-guard exec 原样门链（四层 scope/
    全局 deny-list/时间旅行——guard 单源）；revert 义务落账 timeline。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIXTURE, os.path.join(self.td.name, "G-g1"))
        self.state = os.path.join(self.td.name, "installed.tsv")
        for n in ("curl", "kubectl", "dig"):
            ok, why = tool_install.install(n, "2026-10-18T10:00:00Z",
                                           state_path=self.state)
            assert ok, why

    def timeline_text(self):
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            return f.read()

    def test_delegation_argv_shape(self):
        sp = FakeSpawn()
        rc, _, _ = tool_gate.execute(
            self.gd, "curl", ["-sS", "https://api.shop.example/"],
            "2026-10-18T12:00:00Z", spawn=sp, state_path=self.state)
        self.assertEqual(rc, 0)
        self.assertEqual(len(sp.calls), 1, "门过即恰一次委托")
        argv = sp.calls[0]
        self.assertEqual(argv[:3], [PY, GUARD_ENTRY, "exec"])
        self.assertIn("--goal-dir", argv)
        self.assertEqual(argv[argv.index("--goal-dir") + 1], self.gd)
        self.assertEqual(argv[argv.index("--timestamp") + 1],
                         "2026-10-18T12:00:00Z")
        sep = argv.index("--")
        self.assertEqual(argv[sep + 1:], ["curl", "-sS",
                                          "https://api.shop.example/"])

    def test_card_gate_reject_skips_guard_and_logs(self):
        sp = FakeSpawn()
        before = self.timeline_text()
        rc, _, err = tool_gate.execute(
            self.gd, "metasploit", ["-h"], "2026-10-18T12:00:00Z",
            spawn=sp, state_path=self.state)
        self.assertEqual(rc, 1)
        self.assertEqual(sp.calls, [], "卡层拒=零委托（guard 不被调用）")
        self.assertIn("unknown-tool", err)
        after = self.timeline_text()
        self.assertTrue(after.startswith(before), "既有 timeline 行不可改写")
        self.assertIn("tools-reject", after[len(before):])
        self.assertIn("metasploit", after[len(before):])

    def test_guard_reject_propagates_rc(self):
        sp = FakeSpawn(rc=1, err="REJECT" + chr(9) + "guard" + chr(9)
                       + "界外目标: evil.example")
        rc, _, err = tool_gate.execute(
            self.gd, "curl", ["-sS", "https://evil.example/"],
            "2026-10-18T12:00:00Z", spawn=sp, state_path=self.state)
        self.assertEqual(rc, 1, "guard REJECT 退出码原样传播")
        self.assertIn("界外目标", err)

    def test_success_with_revert_obligation_logged(self):
        sp = FakeSpawn(rc=0)
        rc, _, _ = tool_gate.execute(
            self.gd, "kubectl", ["--context", "eng", "apply", "-f", "job.yml"],
            "2026-10-18T12:00:00Z", spawn=sp, state_path=self.state)
        self.assertEqual(rc, 0)
        added = self.timeline_text()
        self.assertIn("tool-card-exec", added)
        self.assertIn("name=kubectl", added)
        self.assertIn("delete -f", added, "revert 义务核销命令须入账")

    def test_success_readonly_card_no_revert_payload(self):
        sp = FakeSpawn(rc=0)
        rc, _, _ = tool_gate.execute(
            self.gd, "dig", ["+short", "A", "api.shop.example"],
            "2026-10-18T12:00:00Z", spawn=sp, state_path=self.state)
        self.assertEqual(rc, 0)
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            rows = [ln.split(chr(9)) for ln in f.read().splitlines()]
        evrows = [r for r in rows if len(r) > 4 and "tool-card-exec" in r[3]]
        self.assertEqual(len(evrows), 1)
        self.assertEqual(evrows[0][4], "", "只读卡 revert 列空（无义务不虚记）")

    def test_timeline_chain_still_verifies_after_execute(self):
        sp = FakeSpawn(rc=0)
        tool_gate.execute(self.gd, "curl", ["-sS", "https://api.shop.example/"],
                          "2026-10-18T12:00:00Z", spawn=sp, state_path=self.state)
        from ledger import core as ledger_core
        sess = ledger_core.Session(self.gd)
        ok, bad = sess.verify_chain()
        self.assertTrue(ok, "execute 落账后链式哈希必须仍完整: line %s" % bad)


TOOLS_ENTRY = os.path.join(ROOT, "cli", "tanyin-tools")


def tools_cli(*args, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([PY, TOOLS_ENTRY] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env)


class TestToolsCli(unittest.TestCase):
    """③卡片清单命令：list 列卡 / show 查卡详情 / install 装卡验签 /
    verify-lock 全量验签 / exec 执行入口（全走 gate 门链）。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.state = os.path.join(self.td.name, "installed.tsv")
        self.gd = shutil.copytree(FIXTURE, os.path.join(self.td.name, "G-g1"))
        self.env = {"TANYIN_TOOLS_STATE": self.state}

    def test_list_shows_25_cards_with_discipline_columns(self):
        r = tools_cli("list", env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for n in REQUIRED_25:
            self.assertIn(n, r.stdout)
        self.assertIn("tier", r.stdout.lower())
        self.assertIn("rate", r.stdout.lower())
        self.assertIn("risk", r.stdout.lower())
        self.assertIn("25", r.stdout, "清单须报卡计数")

    def test_list_marks_installed_cards(self):
        tool_install.install("curl", "2026-10-18T10:00:00Z",
                             state_path=self.state)
        r = tools_cli("list", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        line = [ln for ln in r.stdout.splitlines()
                if ln.startswith("curl" + chr(9))][0]
        self.assertIn("in-service", line, "在役卡须有标记")

    def test_show_card_detail_full_discipline(self):
        r = tools_cli("show", "nuclei", env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for frag in ("nuclei", "L1", "10/s", "medium", "-rl",
                     "-etags", "dos,intrusive", "w3-1"):
            self.assertIn(frag, r.stdout, "show 详情缺 %r" % frag)

    def test_show_l3_card_discloses_approval_gate(self):
        r = tools_cli("show", "sqlmap", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("L3", r.stdout)
        self.assertIn("审批门", r.stdout)

    def test_show_unknown_card_usage_error(self):
        r = tools_cli("show", "metasploit", env_extra=self.env)
        self.assertEqual(r.returncode, 2)

    def test_install_via_cli_ok_then_reject_unknown(self):
        r = tools_cli("install", "dig", "--timestamp=2026-10-18T10:00:00Z",
                      env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("dig", r.stdout)
        r2 = tools_cli("install", "metasploit",
                       "--timestamp=2026-10-18T10:00:00Z", env_extra=self.env)
        self.assertEqual(r2.returncode, 1)
        self.assertIn("unknown-tool", r2.stdout + r2.stderr)

    def test_verify_lock_all_pass(self):
        r = tools_cli("verify-lock", env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("25", r.stdout)

    def test_verify_lock_tampered_fails(self):
        entries = tool_lock.load(tool_lock.DEFAULT_LOCK_PATH)
        entries["nikto"]["sha256"] = "ab" * 32
        bad = os.path.join(self.td.name, "tools-bad.lock")
        tool_lock.write_entries(bad, entries)
        r = tools_cli("verify-lock", "--lock=" + bad, env_extra=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("nikto", r.stdout + r.stderr)

    def test_exec_not_installed_rejected(self):
        r = tools_cli("exec", "--goal-dir", self.gd,
                      "--timestamp=2026-10-18T12:00:00Z",
                      "--", "curl", "-sS", "https://api.shop.example/",
                      env_extra=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("card-not-installed", r.stdout + r.stderr)

    def test_exec_unknown_rejected(self):
        r = tools_cli("exec", "--goal-dir", self.gd,
                      "--timestamp=2026-10-18T12:00:00Z",
                      "--", "metasploit", "-h", env_extra=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown-tool", r.stdout + r.stderr)

    def test_exec_requires_timestamp(self):
        r = tools_cli("exec", "--goal-dir", self.gd, "--", "curl", "-h",
                      env_extra=self.env)
        self.assertEqual(r.returncode, 2, "EPOCH 缺省退役律：--timestamp 必填")

    def test_usage_no_args(self):
        r = tools_cli()
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
