# -*- coding: utf-8 -*-
"""v0.9d Ship U——ZhulongFire 全站换肤 / 战局总览首页 / 人话律 / 四态纪律 / status.js 单源。

python3 -m unittest tests.test_v09d_skin
依据 docs/superpowers/plans/2026-10-15-v09d-ui.md Ship U + docs/design/tanyin-product-v1.md 界面基线。
约束铁律：页面完全自包含（常驻 0.9c 老进程无 /status.js 路由——五页内嵌字节级副本）、
零框架零 CDN 零外域、浅色默认+深色镜像（localStorage 记忆）、动效全站≤3 处、只读投影零写入。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
STATIC = os.path.join(CLI, "webui", "static")
STATUS_JS = os.path.join(STATIC, "status.js")
PAGES = ("index.html", "coverage.html", "graph.html", "evidence.html", "metrics.html")
PHASES_YAML = os.path.join(HERE, "..", "phases", "phases.yaml")

NAV8 = {"/", "/activity", "/session", "/coverage", "/graph",
        "/evidence", "/metrics", "/experiments"}

# 内嵌副本字节钉标记（五页 <script> 内，段==文件全文字节）
BEGIN_MARK = "/* STATUS-JS:BEGIN */"
END_MARK = "/* STATUS-JS:END */"

CORE_VARS = {"--bg", "--card", "--ink", "--dim", "--line", "--accent",
             "--accent-ink", "--soft", "--ok", "--bad", "--warn",
             "--idle", "--skeleton"}


def _src(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


def _status_js():
    with open(STATUS_JS, encoding="utf-8") as f:
        return f.read()


def _yaml_gates():
    """phases.yaml → [(id, 中文名)，按 states 全序]（防漂移对照真相）。"""
    with open(PHASES_YAML, encoding="utf-8") as f:
        text = f.read()
    sm = re.search(r"^states:\s*\[([^\]]*)\]", text, re.M)
    ids = [p.strip() for p in sm.group(1).split(",")]
    titles = dict(re.findall(r"^  (P[0-9.]+):\s*$\s*\n\s+title:\s*(\S+)", text, re.M))
    return [(i, titles[i]) for i in ids]


class TestStatusJsSingleSource(unittest.TestCase):
    """status.js 单源：九门与 phases.yaml 全序一致；状态语义表集中（ARTEX status.ts 语义）。"""

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(STATUS_JS), "cli/webui/static/status.js 缺席")

    def test_nine_gates_match_phases_yaml(self):
        """九门 id+中文名 == phases.yaml states 全序 + gates.title（顺序/门数/名全等）。"""
        js = _status_js()
        m = re.search(r"TY\.NINE_GATES\s*=\s*\[(.*?)\];", js, re.S)
        self.assertIsNotNone(m, "status.js 缺 TY.NINE_GATES 表")
        got = re.findall(r'\{\s*id:\s*"([^"]+)"\s*,\s*name:\s*"([^"]+)"\s*\}', m.group(1))
        self.assertGreater(len(got), 0, "NINE_GATES 空表")
        want = _yaml_gates()
        self.assertEqual([g[0] for g in got], [w[0] for w in want],
                         "门 id 全序漂移: %s vs yaml %s" % (got, want))
        self.assertEqual([g[1] for g in got], [w[1] for w in want],
                         "门中文名漂移: %s vs yaml %s" % (got, want))
        self.assertIn(("P6.0", "清理门"), got, "清理门 P6.0 缺席")

    def test_state_semantics_tables(self):
        """三张语义表：门态/重放三态/矩阵格态——中文标签+tone 一处定义。"""
        js = _status_js()
        for key, states in (
                ("TY.GATE_STATE", ("PASS", "FAIL", "PENDING")),
                ("TY.REPLAY_STATE", ("reproduced", "not-reproduced",
                                     "manual", "env-diff")),
                ("TY.CELL_STATE", ("cold", "frozen", "empty"))):
            self.assertIn(key, js, "缺语义表 " + key)
        gate = re.search(r"TY\.GATE_STATE\s*=\s*\{(.*?)\};", js, re.S).group(1)
        for st in ("PASS", "FAIL", "PENDING"):
            self.assertIn('"%s"' % st, gate, "GATE_STATE 缺 " + st)
        replay = re.search(r"TY\.REPLAY_STATE\s*=\s*\{(.*?)\};", js, re.S).group(1)
        for lbl in ("已复现", "未复现", "人工", "环境差异", "未重放"):
            self.assertIn(lbl, replay, "REPLAY_STATE 缺中文标签 " + lbl)
        cell = re.search(r"TY\.CELL_STATE\s*=\s*\{(.*?)\};", js, re.S).group(1)
        self.assertIn("欠账空格", cell, "CELL_STATE 缺欠账空格语义")

    def test_status_js_zero_network(self):
        js = _status_js()
        self.assertNotIn("<script src=", js)
        self.assertNotIn("https://", js)
        self.assertNotIn("http://", js.replace("http://www.w3.org", ""))


class TestEmbeddedCopySync(unittest.TestCase):
    """字节钉：五页内嵌 status.js 副本与单源文件全文字节一致（防漂移）。"""

    def test_embedded_equals_file_on_all_pages(self):
        want = _status_js()
        for name in PAGES:
            src = _src(name)
            self.assertIn(BEGIN_MARK, src, name + " 缺内嵌起点标记")
            self.assertIn(END_MARK, src, name + " 缺内嵌终点标记")
            self.assertEqual(src.count(BEGIN_MARK), 1, name + " 内嵌段不唯一")
            seg = src.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0]
            self.assertTrue(seg.startswith("\n"), name + " BEGIN 标记后应换行")
            self.assertTrue(seg.endswith("\n"), name + " END 标记前应换行")
            self.assertEqual(seg[1:], want,
                             name + " 内嵌副本与 status.js 字节漂移（改单源须五页同步）")

    def test_no_script_src_reference(self):
        """自包含律：老进程无 /status.js 路由——页面不得外链引用单源文件。"""
        for name in PAGES:
            self.assertNotIn('src="/status.js"', _src(name), name)


class TestZhulongFireSkin(unittest.TestCase):
    """ZhulongFire：浅色默认+深色镜像（CSS 变量同名成对）、品牌蓝、切换钮、动效≤3。"""

    def test_light_default_brand_blue(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn("--accent:#2563EB", src,
                          name + " 浅色默认缺品牌蓝 #2563EB")
            self.assertRegex(src, r":root\s*\{", name + " 缺 :root 浅色块")

    def test_dark_mirror_same_var_names(self):
        for name in PAGES:
            src = _src(name)
            lm = re.search(r":root\s*\{(.*?)\}", src, re.S)
            dm = re.search(r'html\[data-theme="dark"\]\s*\{(.*?)\}', src, re.S)
            self.assertIsNotNone(lm, name + " 缺 :root 浅色变量块")
            self.assertIsNotNone(dm, name + " 缺深色镜像块")
            light = set(re.findall(r"(--[A-Za-z0-9-]+)\s*:", lm.group(1)))
            dark = set(re.findall(r"(--[A-Za-z0-9-]+)\s*:", dm.group(1)))
            self.assertEqual(light, dark,
                             name + " 变量镜像不齐: %s" % (light ^ dark))
            self.assertTrue(CORE_VARS <= light,
                            name + " 核心变量缺: %s" % (CORE_VARS - light))

    def test_theme_toggle_button_everywhere(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn('id="theme-toggle"', src, name + " 缺主题切换钮")
            self.assertIn("TY.toggleTheme", src, name + " 未接单源切换")

    def test_theme_persist_and_boot(self):
        js = _status_js()
        self.assertIn('TY.THEME_KEY = "tanyin-theme"', js)
        self.assertIn("localStorage", js)
        self.assertIn("getItem", js)
        self.assertIn("setItem", js)
        self.assertIn("TY.bootTheme()", js, "单源须载入即恢复主题（防深色白闪）")
        self.assertIn('setAttribute("data-theme"', js)
        for name in PAGES:
            self.assertIn("TY.syncThemeButton", _src(name),
                          name + " 未同步切换钮文案")

    def test_motion_budget_le_3(self):
        """动效预算：全站（五页 CSS）transition/animation 声明合计 ≤3 处。"""
        total = 0
        for name in PAGES:
            n = len(re.findall(r"(?<![-\w])(?:transition|animation)\s*:", _src(name)))
            total += n
        self.assertLessEqual(total, 3, "动效预算超支: 全站 %d 处 > 3" % total)


class TestNavEightLinks(unittest.TestCase):
    """nav 八链：八视图全站同构（含 /session——只断言存在不断言通）。"""

    def test_all_pages_share_eight_links(self):
        for name in PAGES:
            src = _src(name)
            m = re.search(r"<nav[^>]*>(.*?)</nav>", src, re.S)
            self.assertIsNotNone(m, name + " 缺 nav 块")
            got = set(re.findall(r'href="(/[^"#?]*)"', m.group(1)))
            self.assertEqual(got, NAV8,
                             name + " 导航漂移: %s" % (got ^ NAV8))

    def test_session_link_present(self):
        for name in PAGES:
            self.assertIn('href="/session"', _src(name), name)


class TestBattleOverview(unittest.TestCase):
    """首页重做=战局总览：战斗大卡/九门进度条/KPI 可点过滤/最新发现/预算预警/活动流。"""

    def test_battle_card_nodes(self):
        src = _src("index.html")
        self.assertIn('id="battle-card"', src)
        for nid in ('id="battle-phase"', 'id="battle-duration"',
                    'id="battle-findings"'):
            self.assertIn(nid, src, "战斗大卡缺 " + nid)

    def test_nine_gates_progress_bars(self):
        src = _src("index.html")
        self.assertIn('id="phases"', src)
        self.assertIn("gate-track", src, "九门未进度条化")
        self.assertIn("gate-fill", src)
        self.assertIn("TY.NINE_GATES", src, "九门渲染未走 status.js 单源")

    def test_kpi_clickable_filters(self):
        src = _src("index.html")
        self.assertIn('id="kpi-row"', src)
        self.assertIn('href="/coverage#f=empty"', src, "欠账空格 KPI 未可点过滤")
        self.assertIn('href="/evidence#f=reproduced"', src)
        self.assertIn('href="/evidence#f=not-reproduced"', src)

    def test_filter_targets_implemented(self):
        self.assertIn("hashchange", _src("coverage.html"),
                      "热图页未实现 #f=empty 过滤响应")
        self.assertIn("hashchange", _src("evidence.html"),
                      "证据页未实现 #f= 过滤响应")
        self.assertIn("f=empty", _src("coverage.html"))
        self.assertIn("f=reproduced", _src("evidence.html"))

    def test_latest_findings_list(self):
        src = _src("index.html")
        self.assertIn('id="latest-findings"', src)

    def test_kpi_data_sources(self):
        src = _src("index.html")
        self.assertIn("/api/matrix.json", src, "KPI 欠账数未拉矩阵 API")
        self.assertIn("/api/evidence.json", src, "KPI 证据数未拉证据 API")


class TestPlainLanguageLaw(unittest.TestCase):
    """人话律：每页中文标题+「你在看什么」副题；黑话清零（E-index→证据编号）。"""

    def test_every_page_has_subtitle(self):
        for name in PAGES:
            src = _src(name)
            m = re.search(r"<h1>([^<]+)</h1>", src)
            self.assertIsNotNone(m, name + " 缺中文 H1")
            self.assertTrue(m.group(1).strip(), name + " H1 空")
            self.assertRegex(src, r'class="page-sub"[^>]*>你在看什么：',
                             name + " 缺「你在看什么」副题")

    def test_no_jargon_e_index(self):
        for name in PAGES:
            self.assertNotIn("E-index", _src(name),
                             name + " 黑话未清零（E-index→证据编号）")


class TestFourStateDiscipline(unittest.TestCase):
    """四态纪律：每页骨架/加载/空/错误四态齐（骨架静默占位，无动画）。"""

    def test_four_states_on_every_page(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn("skeleton", src, name + " 缺骨架态")
            self.assertIn("载入中", src, name + " 缺加载态文案")
            self.assertIn('data-state="empty"', src, name + " 缺空态")
            self.assertIn('data-state="error"', src, name + " 缺错误态")
            self.assertIn("TY.setState(", src, name + " 未走单源四态助手")

    def test_error_path_uses_failtext(self):
        for name in PAGES:
            self.assertIn("failText", _src(name),
                          name + " 错误态未用统一文案助手")


class TestMetricsExperimentsUntouched(unittest.TestCase):
    """禁碰钉：metrics.html 的 experiments 节点结构保留（test_exp_registry 同款底线）。"""

    def test_experiments_section_kept(self):
        src = _src("metrics.html")
        self.assertIn('id="experiments"', src)
        self.assertIn("无预登记实验", src)
        self.assertIn("预登记实验", src)


if __name__ == "__main__":
    unittest.main()
