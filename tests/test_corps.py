# -*- coding: utf-8 -*-
"""兵种运行时测试（F4 收尾件·corps.py，TDD 红点先行）。

锚点：
- 对照账 docs/design/2026-10-20-capability-comparison-ledger.md F4:50——
  兵种=六维配置对象（加兵种=加模板零运行时代码）；F9:90 兵种 YAML=配置
  对象单源。五兵种卡已落（297e2b0：recon/enum/exploit/verify/commander，
  tests/test_soldier_cards.py 24 结构测试钉卡面）——本舰把卡从数据变成
  运行时可指派的配置对象。
- 裁决书 §六军团编制六维（permissions/tools/llm_route/backend/trigger/
  artifacts）；总控派单带兵种位=意图 detail 承载（commander 卡纪律 2：
  recon→侦察兵/surface→枚举兵/matrix-test+deep-dive→渗透兵/nday-verify→
  验证官，contracts/01 六 kind）。
- detail 虚拟列先例=[prereq:]/[owner:]/[lease:] 方括号标记（cli/ledger/
  write_cmds.py:501,524-526）——兵种位同形 [corps:<name>]。

测试六群：
① 加载——零配置=五兵种全开（卡面为缺省）；六维字段解析；skill_path
   卡面引用实存；写面白名单自 registry 写命令面派生（不手抄）。
② 路由——意图行带兵种位直读；缺省按 kind 四映射；commander 只经兵种位
   （常驻调度非意图路由）；无路由 kind（authz-diff——F6 在飞）fail-loud
   不静默兜底。
③ 越权拒——authorize 纯函数（执行器前置校验形，guardrail.Admission 同
   构）：面外命令拒+写面越权拒+面内放行；永不 raise。
④ yaml 配置面——裁兵种/改默认路由/收窄工具卡；扩面（放权）拒；未知
   兵种/未知顶级键=fail-loud；显式 --corps 路径加载。
⑤ 面真实——ledger 命令逐条可派发、工具卡逐条在册（与卡面单源一致）。
⑥ 纪律——corps.py 零耦合禁碰面（不 import loop/executor/write_cmds）。
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)

from warrior import corps as corps_mod          # noqa: E402

from ledger import registry                     # noqa: E402
from tools import cards as tool_cards           # noqa: E402

RECON = "pentest-recon"
ENUM = "pentest-enum"
EXPLOIT = "pentest-exploit"
VERIFY = "pentest-verify"
COMMANDER = "pentest-commander"
FIVE = (RECON, ENUM, EXPLOIT, VERIFY, COMMANDER)

# 期望面（与 tests/test_soldier_cards.py 卡面精确集同源——卡面即缺省面）。
EXPECTED_LEDGER = {
    RECON: {"budget-check", "scope-check"},
    ENUM: {"add-asset", "add-fact", "budget-check", "graph-horizon",
           "matrix-gaps", "matrix-init", "matrix-set", "pending-intents",
           "scope-check", "unconsumed-facts"},
    VERIFY: {"pending-intents", "retest-pending", "retest-scan",
             "retest-settle", "set-replay-state"},
    EXPLOIT: {"add-cred", "add-evidence", "add-finding", "budget-check",
              "chain-advance", "chain-create", "graph-paths", "intent-lease",
              "matrix-gaps", "pending-intents", "scope-check"},
    COMMANDER: {"add-intent", "amend-scope", "append-timeline", "approve",
                "budget-check", "converge-check", "graph-horizon",
                "intent-status", "matrix-audit", "matrix-freeze",
                "matrix-gaps", "pending-intents", "retest-pending",
                "set-intent-status", "supersede-finding"},
}
EXPECTED_CARDS = {
    RECON: {"amass", "dig", "dnsrecon", "dnsx", "gau", "httprobe", "httpx",
            "katana", "masscan", "naabu", "nmap", "rustscan", "subfinder",
            "wafw00f", "waybackurls", "whatweb"},
    ENUM: set(),
    VERIFY: set(),
    EXPLOIT: {"arjun", "dirsearch", "feroxbuster", "ffuf", "gobuster",
              "jwt-tool", "kiterunner", "nikto", "nuclei", "sqlmap",
              "sslscan", "testssl"},
    COMMANDER: set(),
}
EXPECTED_WRITES = {
    RECON: set(),
    ENUM: {"add-asset", "add-fact", "matrix-init", "matrix-set"},
    VERIFY: {"set-replay-state", "retest-scan", "retest-settle"},
    EXPLOIT: {"add-cred", "add-evidence", "add-finding", "chain-advance",
              "chain-create"},
    COMMANDER: {"add-intent", "amend-scope", "append-timeline", "approve",
                "matrix-freeze", "set-intent-status", "supersede-finding"},
}


def _row(kind, detail="", iid="INT-1"):
    """意图行（LedgerIO.latest_intents 的 dict 形——17 列子集即可路由）。"""
    return {"id": iid, "kind": kind, "detail": detail, "status": "pending"}


def _write_cfg(text):
    d = tempfile.mkdtemp(prefix="corps-cfg-")
    p = os.path.join(d, "corps.yaml")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


class TestLoadDefaults(unittest.TestCase):
    """① 加载：零配置=五兵种全开，卡面为缺省。"""

    def test_zero_config_five_corps(self):
        rt = corps_mod.load_corps()
        self.assertEqual(rt.enabled(), list(FIVE))

    def test_goal_dir_without_yaml_same_defaults(self):
        d = tempfile.mkdtemp(prefix="corps-goal-")
        rt = corps_mod.load_corps(d)
        self.assertEqual(rt.enabled(), list(FIVE))
        self.assertFalse(os.path.exists(os.path.join(d, "corps.yaml")))

    def test_card_six_dim_fields_parsed(self):
        rt = corps_mod.load_corps()
        c = rt.corps(RECON)
        self.assertEqual(set(c.ledger), EXPECTED_LEDGER[RECON])
        self.assertEqual(set(c.cards), EXPECTED_CARDS[RECON])
        self.assertIn("便宜", c.llm_route)          # 便宜快道
        self.assertEqual(c.backend, "warrior")
        self.assertTrue(c.skill_path.endswith(
            os.path.join(".opencode", "skills", RECON, "SKILL.md")))
        self.assertIn("强道", rt.corps(EXPLOIT).llm_route)
        self.assertTrue(rt.corps(VERIFY).llm_route.startswith("无"))
        self.assertIn("任意", rt.corps(ENUM).llm_route)

    def test_skill_path_files_exist(self):
        """卡面引用实存：每兵种简报模板路径指向真实 SKILL.md。"""
        rt = corps_mod.load_corps()
        for name in rt.enabled():
            self.assertTrue(os.path.isfile(rt.corps(name).skill_path),
                            name + " 简报模板缺失: " + rt.corps(name).skill_path)

    def test_write_allow_derived_from_registry(self):
        """写面白名单=ledger 面 ∩ registry 写命令面（单源派生不手抄）。"""
        rt = corps_mod.load_corps()
        for name in FIVE:
            self.assertEqual(set(rt.corps(name).write_allow),
                             EXPECTED_WRITES[name], name + " 写面白名单≠期望")

    def test_corps_object_immutable_face(self):
        c = corps_mod.load_corps().corps(RECON)
        with self.assertRaises((AttributeError, TypeError)):
            c.ledger.add("add-finding")


class TestResolve(unittest.TestCase):
    """② 路由：兵种位直读优先，缺省 kind 四映射，无路由 fail-loud。"""

    def setUp(self):
        self.rt = corps_mod.load_corps()

    def test_kind_default_routes(self):
        """缺省四映射（commander 卡纪律 2 逐字）：recon/surface/
        matrix-test+deep-dive/nday-verify。"""
        self.assertEqual(self.rt.resolve(_row("recon")).name, RECON)
        self.assertEqual(self.rt.resolve(_row("surface")).name, ENUM)
        self.assertEqual(self.rt.resolve(_row("matrix-test")).name, EXPLOIT)
        self.assertEqual(self.rt.resolve(_row("deep-dive")).name, EXPLOIT)
        self.assertEqual(self.rt.resolve(_row("nday-verify")).name, VERIFY)

    def test_marker_direct_read_wins(self):
        """意图行带兵种位直读（[corps:X] 方括号标记，prereq/owner 同形）。"""
        row = _row("recon", "复核复放 [corps:%s] 优先" % VERIFY)
        self.assertEqual(self.rt.resolve(row).name, VERIFY)

    def test_marker_commander_via_slot_only(self):
        """commander=常驻调度（战役建立即位），只经兵种位指派非 kind 路由。"""
        row = _row("nday-verify", "调度步 [corps:%s]" % COMMANDER)
        self.assertEqual(self.rt.resolve(row).name, COMMANDER)

    def test_marker_survives_lease_marks(self):
        """与 [owner:]/[lease:] 标记共存（领取后整行复制携带兵种位）。"""
        row = _row("surface", "登记 [corps:%s] [owner:W-1][lease:2026-01-01T00:00:00Z]" % ENUM)
        self.assertEqual(self.rt.resolve(row).name, ENUM)

    def test_unrouted_kind_fail_loud(self):
        """authz-diff（F6 业务逻辑层在飞）无缺省兵种——fail-loud 不静默兜底。"""
        with self.assertRaises(corps_mod.CorpsError) as cm:
            self.rt.resolve(_row("authz-diff"))
        self.assertIn("authz-diff", str(cm.exception))

    def test_unknown_kind_fail_loud(self):
        with self.assertRaises(corps_mod.CorpsError):
            self.rt.resolve(_row("bogus-kind"))

    def test_missing_kind_fail_loud(self):
        with self.assertRaises(corps_mod.CorpsError):
            self.rt.resolve({"id": "INT-9", "detail": ""})

    def test_marker_unknown_corps_fail_loud(self):
        with self.assertRaises(corps_mod.CorpsError) as cm:
            self.rt.resolve(_row("recon", "[corps:pentest-ninja]"))
        self.assertIn("pentest-ninja", str(cm.exception))


class TestAuthorize(unittest.TestCase):
    """③ 越权拒：spawn 时权限集外命令直接拒（纯函数，永不 raise）。"""

    def setUp(self):
        self.rt = corps_mod.load_corps()

    def test_write_outside_whitelist_denied(self):
        """写面越权=拒（recon 零写命令；verify 不产发现；exploit 不复放）。"""
        for name, cmd in ((RECON, "add-finding"), (RECON, "add-asset"),
                          (VERIFY, "add-finding"), (EXPLOIT, "set-replay-state"),
                          (ENUM, "add-finding"), (COMMANDER, "add-finding")):
            a = corps_mod.authorize(self.rt.corps(name), cmd)
            self.assertFalse(a.allowed, "%s 越权写命令被放行: %s" % (name, cmd))
            self.assertEqual(a.stage, "write")

    def test_face_outside_denied(self):
        """面外命令拒（recon 不开判定/攻击卡；enum 零工具卡）。"""
        a = corps_mod.authorize(self.rt.corps(RECON), "nuclei")
        self.assertFalse(a.allowed)
        self.assertEqual(a.stage, "face")
        self.assertFalse(corps_mod.authorize(self.rt.corps(ENUM), "subfinder").allowed)
        self.assertFalse(corps_mod.authorize(self.rt.corps(COMMANDER), "sqlmap").allowed)

    def test_in_face_allowed(self):
        for name, cmd in ((RECON, "scope-check"), (RECON, "masscan"),
                          (EXPLOIT, "add-finding"), (EXPLOIT, "nuclei"),
                          (VERIFY, "set-replay-state"),
                          (ENUM, "matrix-init"), (COMMANDER, "approve")):
            a = corps_mod.authorize(self.rt.corps(name), cmd)
            self.assertTrue(a.allowed, "%s 面内命令被拒: %s（%s）" % (name, cmd, a.reason))

    def test_authorize_never_raises(self):
        c = self.rt.corps(RECON)
        for bad in ("", "   ", "unknown-cmd", "ledger-add-finding", None, 3):
            a = corps_mod.authorize(c, bad)
            self.assertFalse(a.allowed)
            self.assertTrue(a.reason)

    def test_runtime_authorize_face(self):
        """运行时便捷面：authorize(command, intent_row) 先路由后执法。"""
        a = self.rt.authorize("add-finding", _row("matrix-test"))
        self.assertTrue(a.allowed)
        a = self.rt.authorize("add-finding", _row("recon"))
        self.assertFalse(a.allowed)


class TestYamlConfig(unittest.TestCase):
    """④ 配置面：裁兵种/改默认路由/禁卡——缺省零配置=五兵种全开。"""

    def test_disabled_corps_trimmed(self):
        p = _write_cfg("disabled:\n  - %s\n" % COMMANDER)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertEqual(rt.enabled(), [RECON, ENUM, EXPLOIT, VERIFY])

    def test_disabled_corps_route_fail_loud(self):
        """裁掉的兵种其 kind 缺省路由随裁（不静默改道）；派单即 fail-loud。"""
        p = _write_cfg("disabled:\n  - %s\n" % EXPLOIT)
        rt = corps_mod.load_corps(corps_path=p)
        with self.assertRaises(corps_mod.CorpsError) as cm:
            rt.resolve(_row("matrix-test"))
        self.assertIn(EXPLOIT, str(cm.exception))

    def test_disabled_corps_slot_fail_loud(self):
        p = _write_cfg("disabled:\n  - %s\n" % EXPLOIT)
        rt = corps_mod.load_corps(corps_path=p)
        with self.assertRaises(corps_mod.CorpsError):
            rt.resolve(_row("recon", "[corps:%s]" % EXPLOIT))

    def test_routes_override(self):
        p = _write_cfg("routes:\n  deep-dive: %s\n" % VERIFY)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertEqual(rt.resolve(_row("deep-dive")).name, VERIFY)
        self.assertEqual(rt.resolve(_row("matrix-test")).name, EXPLOIT)

    def test_route_to_disabled_corps_config_error(self):
        """显式路由指向裁掉兵种=配置矛盾，加载即拒（fail-closed）。"""
        p = _write_cfg("disabled:\n  - %s\nroutes:\n  recon: %s\n" % (RECON, RECON))
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_route_unknown_kind_rejected(self):
        p = _write_cfg("routes:\n  bogus-kind: %s\n" % RECON)
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_route_unknown_corps_rejected(self):
        p = _write_cfg("routes:\n  recon: pentest-ninja\n")
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_corps_cards_narrowing(self):
        """禁卡=逐兵种收窄工具卡面（只收不放）；authorize 随面执法。"""
        p = _write_cfg("corps:\n  %s:\n    cards: [nuclei, nikto]\n" % EXPLOIT)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertEqual(set(rt.corps(EXPLOIT).cards), {"nuclei", "nikto"})
        self.assertTrue(corps_mod.authorize(rt.corps(EXPLOIT), "nuclei").allowed)
        self.assertFalse(corps_mod.authorize(rt.corps(EXPLOIT), "ffuf").allowed)

    def test_corps_cards_widening_rejected(self):
        """扩面（卡面外工具）=放权，拒（配置只收不放律）。"""
        p = _write_cfg("corps:\n  %s:\n    cards: [nuclei, nmap]\n" % EXPLOIT)
        with self.assertRaises(corps_mod.CorpsError) as cm:
            corps_mod.load_corps(corps_path=p)
        self.assertIn("nmap", str(cm.exception))

    def test_corps_llm_route_backend_override(self):
        p = _write_cfg("corps:\n  %s:\n    llm_route: 便宜快道——收窄档\n    backend: warrior\n"
                       % EXPLOIT)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertIn("便宜快道", rt.corps(EXPLOIT).llm_route)

    def test_corps_ledger_narrowing(self):
        p = _write_cfg("corps:\n  %s:\n    ledger: [scope-check]\n" % RECON)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertEqual(set(rt.corps(RECON).ledger), {"scope-check"})
        self.assertFalse(corps_mod.authorize(rt.corps(RECON), "budget-check").allowed)

    def test_corps_ledger_widening_rejected(self):
        p = _write_cfg("corps:\n  %s:\n    ledger: [scope-check, add-finding]\n" % RECON)
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_corps_unknown_name_rejected(self):
        p = _write_cfg("corps:\n  pentest-ninja:\n    backend: warrior\n")
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_unknown_top_level_key_rejected(self):
        p = _write_cfg("disable:\n  - %s\n" % RECON)   # 拼错键=拒（防静默失效）
        with self.assertRaises(corps_mod.CorpsError):
            corps_mod.load_corps(corps_path=p)

    def test_goal_dir_yaml_loaded(self):
        """goal 目录配置面：<goal>/corps.yaml 缺省读取位。"""
        d = tempfile.mkdtemp(prefix="corps-goal-")
        with open(os.path.join(d, "corps.yaml"), "w", encoding="utf-8") as f:
            f.write("disabled:\n  - %s\n" % ENUM)
        rt = corps_mod.load_corps(d)
        self.assertNotIn(ENUM, rt.enabled())
        with self.assertRaises(corps_mod.CorpsError):
            rt.resolve(_row("surface"))

    def test_explicit_path_wins_over_goal_dir(self):
        d = tempfile.mkdtemp(prefix="corps-goal-")
        with open(os.path.join(d, "corps.yaml"), "w", encoding="utf-8") as f:
            f.write("disabled:\n  - %s\n" % RECON)
        p = _write_cfg("disabled:\n  - %s\n" % ENUM)
        rt = corps_mod.load_corps(d, corps_path=p)
        self.assertIn(RECON, rt.enabled())
        self.assertNotIn(ENUM, rt.enabled())

    def test_flow_list_and_comments_tolerated(self):
        p = _write_cfg("# 注释行\ndisabled: [%s]\nroutes: {}   # 空改\n" % VERIFY)
        rt = corps_mod.load_corps(corps_path=p)
        self.assertNotIn(VERIFY, rt.enabled())


class TestFacesReal(unittest.TestCase):
    """⑤ 面真实：运行时对象命令面与注册表单源一致（不发明命令）。"""

    def test_ledger_commands_dispatchable(self):
        rt = corps_mod.load_corps()
        for name in rt.enabled():
            for cmd in rt.corps(name).ledger:
                self.assertIsNotNone(registry.lookup(cmd),
                                     name + " 引用未注册命令: " + cmd)

    def test_tool_cards_registered(self):
        names = set(tool_cards.card_names())
        rt = corps_mod.load_corps()
        for name in rt.enabled():
            for card in rt.corps(name).cards:
                self.assertIsNotNone(tool_cards.get_card(card),
                                     name + " 引用未注册工具卡: " + card)
            self.assertTrue(rt.corps(name).cards <= names)


class TestDiscipline(unittest.TestCase):
    """⑥ 纪律：纯函数面零耦合——不 import loop/executor/write_cmds（禁碰面）。"""

    def test_no_forbidden_imports(self):
        src = open(os.path.join(ROOT, "cli", "warrior", "corps.py"),
                   encoding="utf-8").read()
        for banned in ("from warrior import loop", "import loop",
                       "from warrior import executor", "import executor",
                       "write_cmds", "from ledger import registry as"):
            self.assertNotIn(banned, src, "corps.py 越界耦合: " + banned)

    def test_assembly_doc_names_wiring_points(self):
        """装配文档注释在册：loop 修复舰落舱后总控一行的接线位。"""
        src = open(os.path.join(ROOT, "cli", "warrior", "corps.py"),
                   encoding="utf-8").read()
        self.assertIn("装配", src)
        self.assertIn("resolve", src)
        self.assertIn("authorize", src)

    def test_marker_regex_shape(self):
        """兵种位标记形=[corps:X]（prereq/owner/lease 方括号先例同形）。"""
        self.assertEqual(corps_mod.marker_of("x [corps:pentest-recon] y"),
                         "pentest-recon")
        self.assertEqual(corps_mod.marker_of("[owner:W-1][lease:t]"), "")


if __name__ == "__main__":
    unittest.main()
