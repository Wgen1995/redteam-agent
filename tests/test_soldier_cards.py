# -*- coding: utf-8 -*-
"""兵种包结构测试（F4/F9 兵种卡落地舰，TDD 红点先行）。

锚点：
- 对照账 docs/design/2026-10-20-capability-comparison-ledger.md F4:50 行——首批 5 兵种
  模板（总控/Web渗透/侦察/验证官/报告员），报告员已落（pentest-report=168fc00）；
  F9:90 行——兵种 YAML=配置对象单源。本舰补齐其余五卡（侦察拆测绘/登记两兵
  =F1 枚举流水四段「测绘→登记→覆盖记账→交优先级」的兵种化承接）。
- audit 家底对账（docs/design/2026-10-20-build-master-plan.md R14）——「兵种模板/
  六维配置实为零代码（审计名不副实#2）……验证官兵种升级为设计态记账」=本舰要害。
- 兵种纪律=裁决书 §六（docs/design/2026-10-20-graphled-master-verdict.md:28）：
  六维=权限/工具面/LLM道/后端/触发/产物（+执行后端）；验证官=非LLM复验器。

测试四群：
① 结构——六维 frontmatter 齐备（permissions/tools/llm_route/backend/trigger/artifacts
   +name/description）+卡文三节（职责边界/纪律/交接面）+对照账出处引用。
② 命令面真实——frontmatter tools.ledger 逐条 registry.lookup 可验（不发明命令）；
   工具卡逐条在 tools.cards 注册表；卡文 tanyin-<工具> <子命令> 引用对
   selfcheck.KNOWN_COMMANDS / tools.cli.SUBCOMMANDS；工作流正引用 ⊆ 自身声明面；
   交接面引用命令必须 registry 真有其名。
③ 权限最小化——每卡写面精确等于期望集（tripwire：加写命令=改测试的有意行为）；
   recon 零写命令+纯测绘卡（零判定卡零攻击卡全只读）；五卡写面两两不相交
  （分权执法：登记/复放/产发现/派单审批四权分立）；验证官卡承载 S4 四门+
   REPLAY_CAP+三态词汇。
④ 对照账覆盖+交接链——F4:50 首批五兵种逐一有卡；enum 锚 F1 流水行；触发维度
   对齐 contracts/01 六 kind；交接面后继兵种点名成链。
"""
import importlib
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)

from ledger import registry, selfcheck          # noqa: E402
from tools import cards as tool_cards           # noqa: E402
from tools import cli as tools_cli              # noqa: E402

SKILLS = os.path.join(ROOT, ".opencode", "skills")
LEDGER_DOC = os.path.join(ROOT, "docs", "design", "2026-10-20-capability-comparison-ledger.md")
MASTER_PLAN = os.path.join(ROOT, "docs", "design", "2026-10-20-build-master-plan.md")
CONTRACT_SCHEMA = os.path.join(ROOT, "contracts", "01-ledger-schema.md")
STEER_PY = os.path.join(ROOT, "cli", "warrior", "steer.py")

SIX_DIMENSIONS = ("permissions", "tools", "llm_route", "backend", "trigger", "artifacts")
FRONT_KEYS = {"name", "description"} | set(SIX_DIMENSIONS)

RECON = "pentest-recon"
ENUM = "pentest-enum"
VERIFY = "pentest-verify"
EXPLOIT = "pentest-exploit"
COMMANDER = "pentest-commander"
CARD_FILES = {n: os.path.join(SKILLS, n, "SKILL.md")
              for n in (RECON, ENUM, VERIFY, EXPLOIT, COMMANDER)}

# 期望账本命令面（精确集——最小权限 tripwire）。
EXPECTED_LEDGER = {
    RECON: {"budget-check", "scope-check"},
    ENUM: {"add-asset", "add-fact", "budget-check", "graph-horizon", "matrix-gaps",
           "matrix-init", "matrix-set", "pending-intents", "scope-check",
           "unconsumed-facts"},
    VERIFY: {"pending-intents", "retest-pending", "retest-scan", "retest-settle",
             "set-replay-state"},
    EXPLOIT: {"add-cred", "add-evidence", "add-finding", "budget-check",
              "chain-advance", "chain-create", "graph-paths", "intent-lease",
              "matrix-gaps", "pending-intents", "scope-check"},
    COMMANDER: {"add-intent", "amend-scope", "append-timeline", "approve",
                "budget-check", "converge-check", "graph-horizon", "intent-status",
                "matrix-audit", "matrix-freeze", "matrix-gaps", "pending-intents",
                "retest-pending", "set-intent-status", "supersede-finding"},
}

# 期望工具卡面（精确集）：recon=纯测绘卡；exploit=web 面+判定扫描卡；余零卡。
EXPECTED_CARDS = {
    RECON: {"amass", "dig", "dnsrecon", "dnsx", "gau", "httprobe", "httpx", "katana",
            "masscan", "naabu", "nmap", "rustscan", "subfinder", "wafw00f",
            "waybackurls", "whatweb"},
    ENUM: set(),
    VERIFY: set(),
    EXPLOIT: {"arjun", "dirsearch", "feroxbuster", "ffuf", "gobuster", "jwt-tool",
              "kiterunner", "nikto", "nuclei", "sqlmap", "sslscan", "testssl"},
    COMMANDER: set(),
}

# 期望写面（frontmatter tools.ledger ∩ 写命令面==精确集）。
EXPECTED_WRITES = {
    RECON: set(),
    ENUM: {"add-asset", "add-fact", "matrix-init", "matrix-set"},
    VERIFY: {"set-replay-state", "retest-scan", "retest-settle"},
    EXPLOIT: {"add-cred", "add-evidence", "add-finding", "chain-advance",
              "chain-create"},
    COMMANDER: {"add-intent", "amend-scope", "append-timeline", "approve",
                "matrix-freeze", "set-intent-status", "supersede-finding"},
}

# handler 内写形（retest.py 模块 docstring：②retest-scan=写编排 ③retest-settle=写；
# set-replay-state=读写双态）——registry._WRITER_MODULES 模块位派生不覆盖这三条，
# 并入写面（出处即 retest.py:1-40 docstring，非虚构）。
IN_HANDLER_WRITES = {"retest-scan", "retest-settle", "set-replay-state"}

# 侦察兵禁用卡（判定类/攻击类/sqlmap L3）——「只测绘不判定」的卡面执法。
RECON_DENY_CARDS = {"arjun", "dirsearch", "feroxbuster", "ffuf", "gobuster", "jwt-tool",
                    "kiterunner", "nikto", "nuclei", "nuclei-templates", "sqlmap",
                    "sslscan", "testssl"}

# F4:50 首批五兵种 → 卡位（报告员=既有 pentest-report，168fc00 落）。
F4_FIRST_BATCH = {"总控": COMMANDER, "Web渗透": EXPLOIT, "侦察": RECON,
                  "验证官": VERIFY, "报告员": "pentest-report"}


def _writer_face():
    """写命令面=registry 单源派生（_WRITER_MODULES 模块 HANDLERS 键集）。
    私有属性只读引用（registry.py:22-23 docstring 即此口径），不改运行时。"""
    names = set()
    for m in registry._WRITER_MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        names |= set(getattr(mod, "HANDLERS", {}))
    return names


def _base(names):
    """剔 ledger- 前缀孪生别名（all_commands 同律，registry.py:107-113）。"""
    return {n for n in names
            if not (n.startswith("ledger-") and n[len("ledger-"):] in names)}


def _parse_front(text):
    """frontmatter 微解析（仓内零 yaml 依赖先例——tests 全手解析）。
    形制：顶层 key: 单行值；tools: 嵌套两键 ledger:/cards: 流列表。"""
    fm, key = {}, None
    for ln in text.split("---", 2)[1].splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if ln.startswith("  ") and key:
            body = ln.strip()
            if ":" not in body:
                continue
            k, v = body.split(":", 1)
            if v.strip().startswith("[") and v.strip().endswith("]"):
                vals = [t.strip() for t in v.strip()[1:-1].split(",") if t.strip()]
                fm.setdefault(key, {})[k] = vals
            else:
                fm.setdefault(key, {})[k] = v.strip()
        elif ":" in ln and not ln.startswith(" "):
            key = ln.split(":", 1)[0].strip()
            v = ln.split(":", 1)[1].strip()
            if v.startswith("[") and v.endswith("]"):
                fm[key] = [t.strip() for t in v[1:-1].split(",") if t.strip()]
                key = None
            elif v == "":
                fm[key] = {}
            else:
                fm[key] = v
                key = None
    return fm


def load_card(name):
    if not os.path.isfile(CARD_FILES[name]):
        raise AssertionError("兵种卡缺失: " + CARD_FILES[name])
    with open(CARD_FILES[name], encoding="utf-8") as f:
        txt = f.read()
    parts = txt.split("---", 2)
    if len(parts) < 3:
        raise AssertionError(name + " frontmatter 形缺失（--- 围栏）")
    return txt, _parse_front(txt), parts[2]


def section(body, title):
    """取「## <title>…」节到下一 ## 或文末。"""
    m = re.search(r"^## " + title + r"[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def backticks(text):
    """反引号命令 token（小写字母/数字/连字符——路径与占位符自然排除）。"""
    return set(re.findall(r"`([a-z][a-z0-9-]+)`", text))


class TestCardStructure(unittest.TestCase):
    def test_all_cards_exist(self):
        for name, path in sorted(CARD_FILES.items()):
            self.assertTrue(os.path.isfile(path), "兵种卡缺失: " + path)

    def test_frontmatter_six_dimensions_complete(self):
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, fm, _ = load_card(name)
                self.assertEqual(set(fm), FRONT_KEYS,
                                 name + " frontmatter 键集须=六维+name/description")
                self.assertEqual(fm["name"], name)
                self.assertTrue(str(fm["description"]).strip())
                for dim in SIX_DIMENSIONS:
                    self.assertTrue(str(fm[dim]).strip(), name + " 维度空: " + dim)
                self.assertIsInstance(fm["tools"], dict, name + " tools 须嵌套 ledger/cards")
                self.assertEqual(set(fm["tools"]), {"ledger", "cards"})

    def test_body_three_sections(self):
        """卡文=职责边界/纪律/交接面（任务令形制；pentest-report 同族+交接面显式节）。"""
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, _, body = load_card(name)
                for sec in ("职责边界", "纪律", "交接面"):
                    self.assertIn("## " + sec, body, name + " 缺节: ## " + sec)

    def test_cites_comparison_ledger(self):
        """引用必带出处（对照账纪律）：每卡引用对照账 F4/F9（或 F1）行。"""
        for name in CARD_FILES:
            with self.subTest(card=name):
                txt, _, _ = load_card(name)
                self.assertIn("对照账", txt, name + " 须引对照账出处")
                self.assertRegex(txt, r"F[149](:\d+)?")   # F4/F9（enum 锚 F1 流水行）


class TestCommandFaceReal(unittest.TestCase):
    def test_ledger_commands_registry_lookup_pass(self):
        """tools.ledger 逐条 registry.lookup 可验（任务令：不发明命令）。"""
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, fm, _ = load_card(name)
                face = set(fm["tools"]["ledger"])
                self.assertEqual(face, EXPECTED_LEDGER[name],
                                 name + " 账本命令面≠期望精确集")
                for cmd in face:
                    self.assertIsNotNone(registry.lookup(cmd),
                                         name + " 引用未注册命令: " + cmd)
                self.assertTrue(face <= set(registry.dispatch_face()))

    def test_tool_cards_registered(self):
        """tools.cards 逐条在工具卡注册表（tools.cards 单源）——精确集对照。"""
        names = set(tool_cards.card_names())
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, fm, _ = load_card(name)
                face = set(fm["tools"]["cards"])
                self.assertEqual(face, EXPECTED_CARDS[name], name + " 工具卡面≠期望精确集")
                for c in face:
                    self.assertIsNotNone(tool_cards.get_card(c),
                                         name + " 引用未注册工具卡: " + c)
                self.assertTrue(face <= names)

    def test_tanyin_references_known_subcommands(self):
        """卡文 tanyin-<工具> <子命令> 引用须在已知命令面（selfcheck.KNOWN_COMMANDS
        单源；tanyin-tools 面=tools.cli.SUBCOMMANDS——KNOWN_COMMANDS 无 tools 键，
        卡面引用以 SUBCOMMANDS 常量为验）。"""
        pat = re.compile(r"tanyin-([a-z][a-z0-9-]*)[ \t]+([a-z][a-z0-9-]*)")
        for name in CARD_FILES:
            with self.subTest(card=name):
                txt, _, _ = load_card(name)
                for tool, sub in set(pat.findall(txt)):
                    if tool == "tools":
                        self.assertIn(sub, tools_cli.SUBCOMMANDS,
                                      "tanyin-tools 子命令不存在: " + sub)
                    else:
                        self.assertIn(sub, selfcheck.KNOWN_COMMANDS[tool],
                                      "tanyin-" + tool + " 子命令不存在: " + sub)

    def test_workflow_positive_refs_within_declared_face(self):
        """工作流节反引号正引用：账本命令 ⊆ 自身声明面；工具卡 ⊆ 自身声明卡
        （工作流=自己动手的动作面——越面引用即红）。"""
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, fm, body = load_card(name)
                flow = section(body, "工作流")
                toks = backticks(flow)
                known = _base(set(registry.dispatch_face()))
                for t in toks & known:
                    self.assertIn(t, fm["tools"]["ledger"],
                                  name + " 工作流越面引用账本命令: " + t)
                card_names = set(tool_cards.card_names())
                for t in toks & card_names:
                    self.assertIn(t, fm["tools"]["cards"],
                                  name + " 工作流越面引用工具卡: " + t)

    def test_handoff_refs_are_real_commands(self):
        """交接面引用既有命令真实存在——registry.lookup 可验（任务令原文；
        交接面可提后继兵种的命令（协作描述），但必须 registry 真有其名）。"""
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, _, body = load_card(name)
                toks = backticks(section(body, "交接面"))
                known = _base(set(registry.dispatch_face()))
                for t in toks & known:
                    self.assertIsNotNone(registry.lookup(t),
                                         name + " 交接面引用未注册命令: " + t)

    def test_commander_steer_words_match_runtime(self):
        """总控卡 warrior-steer/warrior-stop 事件词须与 cli/warrior/steer.py 单源
        词表一致（F4:50「总控兵种走 steer 通道派单」）。"""
        with open(STEER_PY, encoding="utf-8") as f:
            steer_src = f.read()
        _, _, body = load_card(COMMANDER)
        for word in ("warrior-steer", "warrior-stop"):
            self.assertIn(word, steer_src, "steer.py 事件词缺失: " + word)
            self.assertIn(word, body, "总控卡缺 steer 事件词: " + word)


class TestPermissionMinimization(unittest.TestCase):
    def test_each_card_write_face_exact(self):
        """写面精确集（最小权限 tripwire）：tools.ledger ∩ 写命令面==期望集。"""
        writer = _base(_writer_face()) | IN_HANDLER_WRITES
        for name in CARD_FILES:
            with self.subTest(card=name):
                _, fm, _ = load_card(name)
                face = set(fm["tools"]["ledger"])
                writes = face & writer
                self.assertEqual(writes, EXPECTED_WRITES[name],
                                 name + " 写面≠最小期望集: " + repr(writes))

    def test_recon_zero_write_commands(self):
        """侦察兵零写命令（只测绘不判定——产物=底稿交枚举兵登记）。"""
        _, fm, _ = load_card(RECON)
        writer = _base(_writer_face()) | IN_HANDLER_WRITES
        self.assertEqual(set(fm["tools"]["ledger"]) & writer, set(),
                         "侦察兵不得持写命令")

    def test_recon_cards_readonly_mapping_only(self):
        """侦察兵工具卡全只读（零核销义务=零副作用）+零判定卡零攻击卡。"""
        _, fm, _ = load_card(RECON)
        for c in fm["tools"]["cards"]:
            card = tool_cards.get_card(c)
            self.assertTrue(card.revert.startswith("none(只读"),
                            c + " 非只读卡: " + card.revert)
            self.assertIn(card.category, ("recon", "osint", "web"),
                          c + " 类别越测绘面: " + card.category)
            self.assertNotIn(c, RECON_DENY_CARDS, "侦察兵持判定/攻击卡: " + c)

    def test_enum_exploit_commander_no_foreign_writes(self):
        """分权否定面：enum 不产发现不派单；exploit 不审批不改判不派单不复放；
        总控不产发现不产资产不复放。"""
        writer = _base(_writer_face()) | IN_HANDLER_WRITES
        faces = {n: set(load_card(n)[1]["tools"]["ledger"]) for n in CARD_FILES}
        self.assertEqual(faces[ENUM] & {"add-finding", "add-evidence", "add-cred",
                                        "add-intent", "approve", "supersede-finding",
                                        "amend-scope", "matrix-freeze",
                                        "set-replay-state"}, set())
        self.assertEqual(faces[EXPLOIT] & {"approve", "supersede-finding", "amend-scope",
                                           "add-intent", "set-replay-state",
                                           "matrix-freeze", "add-asset"}, set())
        self.assertEqual(faces[COMMANDER] & {"add-asset", "add-fact", "add-finding",
                                             "add-evidence", "add-cred",
                                             "set-replay-state", "retest-scan",
                                             "retest-settle"}, set())
        self.assertEqual(faces[VERIFY] & writer - EXPECTED_WRITES[VERIFY], set(),
                         "验证官不得持复放三件外的任何写命令")

    def test_write_faces_pairwise_disjoint(self):
        """五卡写面两两不相交——登记/复放/产发现/派单审批四权分立（军团纪律）。"""
        names = sorted(CARD_FILES)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                wa = set(load_card(a)[1]["tools"]["ledger"])
                wb = set(load_card(b)[1]["tools"]["ledger"])
                writer = _base(_writer_face()) | IN_HANDLER_WRITES
                overlap = (wa & writer) & (wb & writer)
                self.assertEqual(overlap, set(),
                                 a + " 与 " + b + " 写面重叠: " + repr(overlap))

    def test_verify_body_carries_s4_and_three_states(self):
        """验证官卡承载 F10 复放纪律词汇：S4 四门+REPLAY_CAP+三态（audit
        「验证官兵种零码」的对账件——卡文与 tanyin-replay 执法面同词）。"""
        txt, _, body = load_card(VERIFY)
        for word in ("授权窗", "危险方法", "次数帽", "REPLAY_CAP", "scope 单源",
                     "reproduced", "not-reproduced", "env-diff",
                     "VERIFIED", "REJECTED", "REPAIRED"):
            self.assertIn(word, txt, "验证官卡缺执法词汇: " + word)
        self.assertIn("非LLM", body, "验证官=非LLM复验器（裁决书§六）")

    def test_exploit_cards_web_domain_only(self):
        """渗透兵卡面限 web/判定扫描两类——不触横移/容器/云（首批域纪律）。"""
        _, fm, _ = load_card(EXPLOIT)
        for c in fm["tools"]["cards"]:
            card = tool_cards.get_card(c)
            self.assertIn(card.category, ("web", "vuln-scan"),
                          c + " 越 Web 渗透域: " + card.category)


class TestLedgerGapCoverage(unittest.TestCase):
    def _ledger_text(self):
        with open(LEDGER_DOC, encoding="utf-8") as f:
            return f.read()

    def test_f4_first_batch_five_soldiers_all_carded(self):
        """对照账 F4:50 缺口行「首批5兵种模板」逐一有卡（enum=侦察流水的
        测绘/登记拆兵，F1 承接；不虚构行外兵种）。"""
        txt = self._ledger_text()
        self.assertIn("首批5兵种模板", txt, "对照账 F4 行锚文缺失")
        for cn_name, card in F4_FIRST_BATCH.items():
            self.assertIn(cn_name, txt, "对照账缺兵种名: " + cn_name)
            self.assertTrue(os.path.isfile(os.path.join(SKILLS, card, "SKILL.md")),
                            "首批兵种无卡: " + cn_name + "→" + card)

    def test_enum_anchored_to_f1_pipeline(self):
        """枚举兵锚 F1 枚举流水四段（测绘→登记→覆盖记账→交优先级）——不虚构。"""
        txt, fm, _ = load_card(ENUM)
        self.assertIn("F1", txt, "枚举兵须锚 F1 流水行")
        ledger_txt = self._ledger_text()
        self.assertIn("## F1 枚举流水", ledger_txt, "对照账 F1 节缺失")
        self.assertIn("测绘→登记→覆盖记账→交优先级", ledger_txt, "F1 四段锚文缺失")

    def test_trigger_kinds_match_contract(self):
        """触发维度对齐 contracts/01 六 kind（recon/surface/matrix-test/deep-dive/
        authz-diff/nday-verify）——意图行带兵种位（F4:50）。"""
        with open(CONTRACT_SCHEMA, encoding="utf-8") as f:
            schema = f.read()
        # intents 表 kind 行=六 kind 中含 recon/surface 的枚举行（scope/facts
        # 表亦有 kind 枚举行——按 recon 锚定 intents 行，不取首个误配）。
        kinds = set()
        for m in re.finditer(r"kind \| 枚举 \| ∈\{([a-z\-/,]+)\}", schema):
            ks = {k for part in m.group(1).split(",") for k in part.split("/")}
            if "recon" in ks and "surface" in ks:
                kinds = ks
        self.assertTrue(kinds, "contracts/01 intents kind 枚举行缺失")
        expect = {RECON: "recon", ENUM: "surface", EXPLOIT: "matrix-test",
                  VERIFY: "nday-verify"}
        for name, kind in expect.items():
            self.assertIn(kind, kinds, "契约缺 kind: " + kind)
            _, fm, _ = load_card(name)
            self.assertIn(kind, str(fm["trigger"]),
                          name + " 触发维度缺意图 kind: " + kind)
        _, fm_c, _ = load_card(EXPLOIT)
        self.assertIn("deep-dive", str(fm_c["trigger"]), "渗透兵触发缺 deep-dive")

    def test_verify_card_answers_audit_zero_code(self):
        """闭环 audit 发现：build-master-plan R14「兵种模板/六维配置实为零代码
        ……验证官兵种升级为设计态记账」——验证官卡落地=该发现的补件。"""
        with open(MASTER_PLAN, encoding="utf-8") as f:
            plan = f.read()
        self.assertIn("兵种模板/六维配置实为零代码", plan, "audit 零码发现锚文缺失")
        self.assertIn("验证官兵种", plan, "audit 验证官发现锚文缺失")
        txt, _, _ = load_card(VERIFY)
        self.assertIn("零代码", txt, "验证官卡须对账 audit 零码发现")


class TestHandoffChain(unittest.TestCase):
    def test_handoff_successors_named(self):
        """交接面后继点名成链：recon→enum→exploit→verify→report；总控点名全四兵
        （军团编制=分工流水，交接断链=漏报源头）。"""
        def handoff(name):
            _, _, body = load_card(name)
            sec = section(body, "交接面")
            self.assertTrue(sec.strip(), name + " 交接面空")
            return sec
        self.assertIn(ENUM, handoff(RECON))
        for succ in (EXPLOIT, VERIFY):
            self.assertIn(succ, handoff(ENUM), "枚举兵交接面缺后继: " + succ)
        self.assertIn(VERIFY, handoff(EXPLOIT), "渗透兵须交验证官（发现必复验）")
        self.assertIn("pentest-report", handoff(VERIFY), "验证官须交报告员")
        sec = handoff(COMMANDER)
        for soldier in (RECON, ENUM, EXPLOIT, VERIFY):
            self.assertIn(soldier, sec, "总控交接面缺兵种: " + soldier)

    def test_recon_pleads_no_judgment(self):
        """侦察兵卡文须显式「只测绘不判定」（任务令①的原话纪律）。"""
        txt, _, _ = load_card(RECON)
        self.assertIn("只测绘不判定", txt)

    def test_enum_registers_into_ledger(self):
        """枚举兵卡文须显式登记纪律（面显形+登记进账本——任务令②原话）。"""
        txt, fm, _ = load_card(ENUM)
        self.assertIn("登记", txt)
        self.assertIn("add-asset", txt + str(fm["tools"]))


if __name__ == "__main__":
    unittest.main()
