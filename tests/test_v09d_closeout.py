# -*- coding: utf-8 -*-
"""v0.9d 收口批（closeout）—— docs/superpowers/plans/2026-10-15-v09d-closeout.md 六项 TDD 钉。

python3 -m unittest tests.test_v09d_closeout
范围（E3 裁决 + 主会话续裁决）：
  1. status.js 全站切外链：七页引用存在+唯一+（server 已有字节伺服）；
     语言律新触发器：任何 ≥40 行共享 JS 不许内嵌出现于 ≥3 页（修完应零命中）；
     顺修 TY.bootTheme() 被调用但未定义的运行时 bug（定义钉——行为=载入即恢复主题）。
  2. 侧栏骨架（ui-design-v1 冻结）：左三分组 看战况/看战果/管战场 + 顶栏战局切换/主题
     + 窄屏可折叠（checkbox 纯 CSS，零动效）。
  3. 12 级灰阶 --g1..--g12 浅深双主题镜像（浅 g1 最浅→g12 最深；深主题反向=镜像）
     + 灰系核心变量挂灰阶 + 圆角 --radius:8px 统一（零裸 px 圆角）。
  4. NAV 每链可达：真 server 九链全查（八路由 200/302 + 设置占位链 /#settings→/ 200
     + index 落占位卡）。
  5. 人话律词表：禁词全站零出现（七页+status.js）+ 替词首现括号注。
  6. 总览最新发现按 finding-stream-priority：severity 徽章+高危置顶+可点跳证据卡
     （/evidence#f=<发现号> 锚定）；evidence_view 增 4 只读字段（主会话裁决①）。
律：Python 3.9 纯 stdlib、只读投影零写入、TDD 先红后绿。
"""
import http.client
import os
import re
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

STATIC = os.path.join(CLI, "webui", "static")
STATUS_JS = os.path.join(STATIC, "status.js")
PAGES = ("index.html", "activity.html", "session.html", "coverage.html",
         "graph.html", "evidence.html", "metrics.html")
NAV8 = {"/", "/activity", "/session", "/coverage", "/graph",
        "/evidence", "/metrics", "/experiments"}
GRAY = ["--g%d" % i for i in range(1, 13)]
CORE_ON_GRAY = ("--bg", "--card", "--ink", "--dim", "--line",
                "--skeleton", "--idle")

BANNED = ("McNemar", "池化", "消格", "置格", "预登记", "双臂",
          "E-index", "fd-卡片")
REPLACEMENTS = ("显著性检验", "合并统计", "已测格", "待测格", "提前登记",
                "对照组与试验组", "证据编号", "发现卡")

TS = "2026-10-15T00:00:00Z"


def _src(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


def _js():
    with open(STATUS_JS, encoding="utf-8") as f:
        return f.read()


def _vars(block):
    """CSS 变量块 → {名: 值}（值截至 ; 或 }）。"""
    return dict((m.group(1), m.group(2).strip())
                for m in re.finditer(r"(--[A-Za-z0-9-]+)\s*:\s*([^;}]+)", block))


def _lum(hexv):
    h = hexv.strip()
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---------------------------------------------------------------------------
# 1. status.js：bootTheme 定义钉 + 外链切换 + 共享 JS 内嵌触发器
# ---------------------------------------------------------------------------

class TestStatusJsBootTheme(unittest.TestCase):
    """顺修 bug：TY.bootTheme() 被调用但从未定义（每页尾部抛 TypeError）。
    行为正确=载入即恢复 localStorage 主题（浅色默认，深色用户不白闪）。"""

    def test_boottheme_defined_as_function(self):
        js = _js()
        self.assertRegex(js, r"TY\.bootTheme\s*=\s*function",
                         "TY.bootTheme 未定义为函数（调用即 TypeError）")

    def test_boottheme_restores_saved_theme(self):
        js = _js()
        m = re.search(r"TY\.bootTheme\s*=\s*function[^;]*;", js)
        self.assertIsNotNone(m)
        body = m.group(0)
        self.assertIn("TY.savedTheme", body, "bootTheme 须读记忆主题")
        self.assertIn("TY.applyTheme", body, "bootTheme 须套用主题")

    def test_boottheme_still_booted(self):
        self.assertIn("TY.bootTheme();", _js(), "载入即恢复主题的调用不得删")


class TestExternalStatusJs(unittest.TestCase):
    """E3 F2 裁决：六页删内嵌副本改外链；七页统一「引用存在+引用唯一」。"""

    def test_every_page_references_external_status_js(self):
        for name in PAGES:
            src = _src(name)
            self.assertEqual(src.count('<script src="/status.js"></script>'), 1,
                             name + " 须外链 /status.js 恰一次")

    def test_reference_in_head(self):
        for name in PAGES:
            src = _src(name)
            head = src.split("</head>")[0]
            self.assertIn('<script src="/status.js"></script>', head,
                          name + " 外链须在 <head>（早于正文绘制）")

    def test_no_embedded_copy_left(self):
        for name in PAGES:
            self.assertNotIn("/* STATUS-JS:BEGIN */", _src(name),
                             name + " 内嵌副本未删净")
            self.assertNotIn("/* STATUS-JS:END */", _src(name), name)


class TestSharedJsInlineTrigger(unittest.TestCase):
    """语言律新触发器：任何 ≥40 行共享 JS 不许内嵌出现于 ≥3 页（全站零命中）。"""

    @staticmethod
    def _inline_blocks(src):
        out = []
        for m in re.finditer(r"<script>(.*?)</script>", src, re.S):
            lines = [ln.rstrip() for ln in m.group(1).strip().split("\n")]
            out.append((len(lines), "\n".join(lines).strip()))
        return out

    def test_no_shared_block_ge40_lines_in_3_pages(self):
        shared = {}
        for name in PAGES:
            for nlines, norm in self._inline_blocks(_src(name)):
                if nlines >= 40:
                    shared.setdefault(norm, set()).add(name)
        hits = {k: v for k, v in shared.items() if len(v) >= 3}
        self.assertEqual(hits, {},
                         "≥40 行共享 JS 内嵌于 ≥3 页: %s" %
                         {tuple(sorted(v))[:3] for v in hits.values()})


# ---------------------------------------------------------------------------
# 2. 侧栏骨架（三分组 + 顶栏 + 响应式折叠）
# ---------------------------------------------------------------------------

class TestSidebarSkeleton(unittest.TestCase):
    """ui-design-v1：左三分组 看战况[总览/活动/会话/热图/十边/证据]
    看战果[度量/实验] 管战场[设置占位]；顶栏战局切换+主题；窄屏可折叠。"""

    @staticmethod
    def _groups(src):
        return {t.strip(): b for t, b in re.findall(
            r'<div class="nav-group"[^>]*>\s*<h3[^>]*>([^<]+)</h3>(.*?)</div>',
            src, re.S)}

    def test_sidebar_three_groups_all_pages(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn('<aside id="side">', src, name + " 缺左侧栏")
            by_title = self._groups(src)
            for g in ("看战况", "看战果", "管战场"):
                self.assertIn(g, by_title, name + " 缺侧栏分组 " + g)

    def test_group_links(self):
        for name in PAGES:
            by_title = self._groups(_src(name))
            war = set(re.findall(r'href="(/[^"#?]*)"',
                                 by_title.get("看战况", "")))
            fruit = set(re.findall(r'href="(/[^"#?]*)"',
                                   by_title.get("看战果", "")))
            self.assertEqual(war, {"/", "/activity", "/session", "/coverage",
                                   "/graph", "/evidence"},
                             name + " 看战况组六链漂移: %s" % war)
            self.assertEqual(fruit, {"/metrics", "/experiments"},
                             name + " 看战果组两链漂移: %s" % fruit)
            self.assertIn('href="/#settings"', by_title.get("管战场", ""),
                          name + " 管战场组缺设置占位链 /#settings")

    def test_single_nav_block(self):
        for name in PAGES:
            self.assertEqual(_src(name).count("<nav"), 1,
                             name + " 须恰一个 nav 块（侧栏导航）")

    def test_nav_extract_still_nav8(self):
        """旧 NAV8 钉兼容：#settings 带 # 不入路径集合——抽取集恰为八链。"""
        for name in PAGES:
            m = re.search(r"<nav[^>]*>(.*?)</nav>", _src(name), re.S)
            self.assertIsNotNone(m, name)
            got = set(re.findall(r'href="(/[^"#?]*)"', m.group(1)))
            self.assertEqual(got, NAV8, name + " 导航漂移: %s" % (got ^ NAV8))

    def test_topbar_battle_switch_and_theme(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn('id="topbar"', src, name + " 缺顶栏")
            top = src.split('id="topbar"', 1)[1].split("</header>", 1)[0]
            self.assertIn('id="battle-switch"', top, name + " 顶栏缺战局切换")
            self.assertIn('id="theme-toggle"', top, name + " 顶栏缺主题切换")
            self.assertRegex(top, r"<h1>[^<]+</h1>", name + " 顶栏缺 H1")
            self.assertIn("你在看什么：", top, name + " 顶栏缺人话律副题")

    def test_battle_switch_wired_to_session_api(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn("/api/session.json", src,
                          name + " 战局切换未拉会话 API")
            self.assertIn('"/session?battle=" + ', src,
                          name + " 战局切换未跳 /session?battle=N")

    def test_responsive_collapse(self):
        for name in PAGES:
            src = _src(name)
            self.assertIn('id="side-check"', src, name + " 缺折叠 checkbox")
            self.assertIn('id="side-toggle"', src, name + " 缺折叠开关钮")
            css = src.split("<style>")[1].split("</style>")[0]
            self.assertIn(".side-check:checked", css, name + " 折叠态未接线")
            self.assertRegex(css, r"@media\s*\(\s*max-width", name + " 缺窄屏断点")
            self.assertIn("#side { display:none; }", css,
                          name + " 窄屏侧栏须默认收起")

    def test_collapse_zero_motion(self):
        """折叠=纯 display 切换：本批不新增动效（全站预算≤3 不变）。"""
        total = 0
        for name in PAGES:
            css = _src(name).split("<style>")[1].split("</style>")[0]
            total += len(re.findall(
                r"(?<![-\w])(?:transition|animation)\s*:", css))
        self.assertLessEqual(total, 3, "动效预算超支: %d > 3" % total)


# ---------------------------------------------------------------------------
# 3. 12 级灰阶 + 圆角 8px 统一
# ---------------------------------------------------------------------------

class TestGrayTokens(unittest.TestCase):
    """--g1..--g12 浅深双主题镜像：浅 g1 最浅→g12 最深；深主题反向（镜像）。
    灰系核心变量挂灰阶；--radius:8px；零裸 px 圆角。"""

    @staticmethod
    def _theme_vars(src, dark):
        if dark:
            m = re.search(r'html\[data-theme="dark"\]\s*\{(.*?)\}', src, re.S)
        else:
            m = re.search(r":root\s*\{(.*?)\}", src, re.S)
        return _vars(m.group(1)) if m else None

    def test_gray_tokens_both_themes_all_pages(self):
        for name in PAGES:
            for dark in (False, True):
                v = self._theme_vars(_src(name), dark)
                self.assertIsNotNone(v, name + (" 缺深色块" if dark else " 缺 :root"))
                for g in GRAY:
                    self.assertIn(g, v, "%s %s缺 %s" % (name, "深主题 " if dark else "", g))
                self.assertEqual(len({v[g] for g in GRAY}), 12,
                                 name + " 灰阶 12 值须两两不同")

    def test_light_ramp_and_dark_mirror(self):
        for name in PAGES:
            light = self._theme_vars(_src(name), False)
            dark = self._theme_vars(_src(name), True)
            ll = [_lum(light[g]) for g in GRAY]
            dl = [_lum(dark[g]) for g in GRAY]
            for i in range(11):
                self.assertGreater(ll[i], ll[i + 1],
                                   name + " 浅色灰阶 g%d→g%d 须渐深" % (i + 1, i + 2))
                self.assertLess(dl[i], dl[i + 1],
                                name + " 深色灰阶 g%d→g%d 须镜像渐浅" % (i + 1, i + 2))
            self.assertGreater(_lum(light["--g1"]), _lum(dark["--g1"]),
                               name + " 浅 g1 须亮于深 g1（镜像律）")

    def test_core_vars_mounted_on_gray(self):
        for name in PAGES:
            for dark in (False, True):
                v = self._theme_vars(_src(name), dark)
                for cv in CORE_ON_GRAY:
                    self.assertRegex(v[cv], r"^var\(--g(\d|1[0-2])\)$",
                                     "%s %s %s 未挂灰阶" % (name, "深" if dark else "浅", cv))

    def test_radius_token_and_no_raw_px_radius(self):
        for name in PAGES:
            src = _src(name)
            css = src.split("<style>")[1].split("</style>")[0]
            self.assertEqual(css.count("--radius:8px"), 2,
                             name + " 浅/深主题各须 --radius:8px")
            raw = re.findall(r"border-radius:\s*([0-9.]+px)", css)
            self.assertEqual(raw, [], name + " 残留裸 px 圆角: %s" % raw)
            self.assertGreaterEqual(css.count("var(--radius)"), 1,
                                    name + " 未使用 --radius 令牌")


# ---------------------------------------------------------------------------
# 4. NAV 每链可达（真 server 九链全查）
# ---------------------------------------------------------------------------

class _ServerBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        from webui import server as srv_mod
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.td.name,
                                       tail=3, poll_s=0.05, keepalive_s=1.0)
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _get(self, path, timeout=5):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path)
        return conn, conn.getresponse()


class TestNavNineLinksReachable(_ServerBase):
    """每链必可达：八路由 200/302 + /status.js 200 + 设置占位链 /#settings→/ 200
    且 index 落设置占位卡（主会话裁决）。"""

    def test_eight_routes_reachable(self):
        want_html = ("/", "/activity", "/session", "/coverage",
                     "/graph", "/evidence", "/metrics")
        for p in want_html:
            conn, resp = self._get(p)
            self.assertEqual(resp.status, 200, p)
            self.assertTrue(resp.getheader("Content-Type").startswith("text/html"), p)
            resp.read()
            conn.close()

    def test_experiments_redirect(self):
        conn, resp = self._get("/experiments")
        self.assertEqual(resp.status, 302)
        self.assertEqual(resp.getheader("Location"), "/metrics#experiments")
        resp.read()
        conn.close()

    def test_status_js_served_bytes(self):
        conn, resp = self._get("/status.js")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type")
                        .startswith("application/javascript"))
        body = resp.read()
        conn.close()
        with open(STATUS_JS, "rb") as f:
            self.assertEqual(body, f.read(), "/status.js 须字节级伺服单源文件")

    def test_settings_placeholder_reachable(self):
        conn, resp = self._get("/")
        self.assertEqual(resp.status, 200)
        body = resp.read().decode("utf-8")
        conn.close()
        self.assertIn('id="settings"', body, "index 缺设置占位卡")
        self.assertIn('href="/#settings"', body, "侧栏设置链未挂 /#settings")
        self.assertRegex(body, r'id="settings"[\s\S]{0,400}占位',
                         "设置卡须明示占位语义")

    def test_nav_links_marked_reachable_all(self):
        """九链可达（含设置占位链）：从页面 nav 抽链接，逐链打真 server。"""
        conn, resp = self._get("/")
        body = resp.read().decode("utf-8")
        conn.close()
        m = re.search(r"<nav[^>]*>(.*?)</nav>", body, re.S)
        self.assertIsNotNone(m)
        self.assertIn('href="/#settings"', m.group(1),
                      "第九链（设置占位 /#settings）缺席")
        paths = set(re.findall(r'href="(/[^"#?]*)"', m.group(1)))
        self.assertEqual(paths, NAV8, "八路径链漂移: %s" % sorted(paths))
        paths.add("/")                       # /#settings 占位链的可达面=/
        for p in sorted(paths):
            conn, resp = self._get(p)
            self.assertIn(resp.status, (200, 302), p)
            resp.read()
            conn.close()


# ---------------------------------------------------------------------------
# 5. 人话律禁词替词表
# ---------------------------------------------------------------------------

class TestPlainLanguageLaw(unittest.TestCase):
    """禁词全站零出现（七页+status.js）+ 替词首现括号注（用到的替词须带注）。"""

    def test_banned_words_zero_site_wide(self):
        targets = [(n, _src(n)) for n in PAGES] + [("status.js", _js())]
        for name, src in targets:
            for w in BANNED:
                self.assertNotIn(w, src,
                                 "%s 禁词未清零: %s（人话律词表）" % (name, w))

    def test_bare_fd_word_zero(self):
        """fd 裸词（小写、词边界）清零——FD- 大写编号是账本 ID 不算黑话。"""
        for name in PAGES:
            self.assertIsNone(re.search(r"(?<![A-Za-z-])fd(?![A-Za-z-])",
                                        _src(name)),
                              name + " 残留裸词 fd（→发现卡）")

    def test_replacement_first_occurrence_annotated(self):
        for name in PAGES:
            src = _src(name)
            for term in REPLACEMENTS:
                if term in src:
                    self.assertRegex(
                        src, re.escape(term) + r"[^（]{0,6}（",
                        name + " 替词 " + term + " 缺首现括号注")


# ---------------------------------------------------------------------------
# 6. 发现流 finding-stream-priority + evidence_view 四字段
# ---------------------------------------------------------------------------

def _row(tname, **kw):
    from ledger import core
    r = [""] * len(core.TABLES[tname])
    for k, v in kw.items():
        r[core.TABLES[tname].index(k)] = str(v)
    return r


class TestEvidenceViewFindingFields(unittest.TestCase):
    """主会话裁决①：evidence_view 卡片增 4 只读字段（findings 行就在手边）。"""

    def setUp(self):
        from ledger import core
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        gd = os.path.join(self.td.name, "G-cl")
        os.makedirs(gd)
        core.write_tsv(os.path.join(gd, "findings.tsv"), [_row(
            "findings.tsv", id="FD-cl-0001", title="注入点占位", impact="高",
            status="open", affected_asset_id="AST-cl-0001",
            schema_version="2", created=TS)])
        core.write_tsv(os.path.join(gd, "E-index.tsv"), [_row(
            "E-index.tsv", id="EV-cl-0001", title="响应捕获", observed_at=TS,
            network_position="dmz", repro_command="curl -i http://x/",
            repro_kind="single", content_hash_raw="a" * 64,
            content_hash_norm="b" * 64, linked_finding="FD-cl-0001",
            schema_version="2", created=TS)])
        self.gd = gd

    def test_cards_carry_finding_fields(self):
        from webui import projections as proj_mod
        cards = proj_mod.evidence_view(self.gd)["cards"]
        self.assertEqual(len(cards), 1)
        c = cards[0]
        self.assertEqual(c["finding_title"], "注入点占位")
        self.assertEqual(c["finding_impact"], "高")
        self.assertEqual(c["finding_status"], "open")
        self.assertEqual(c["finding_asset"], "AST-cl-0001")

    def test_missing_finding_degrades_to_empty(self):
        from webui import projections as proj_mod
        os.remove(os.path.join(self.gd, "findings.tsv"))
        c = proj_mod.evidence_view(self.gd)["cards"][0]
        self.assertEqual(c["finding_impact"], "")
        self.assertEqual(c["finding_title"], "")


class TestFindingStreamPriority(unittest.TestCase):
    """总览最新发现：severity 徽章+高危置顶+可点跳证据卡（/evidence#f=<发现号>）。"""

    def test_severity_order_and_badge(self):
        src = _src("index.html")
        self.assertIn("SEV_ORDER", src, "缺 severity 排序表（高危置顶）")
        self.assertIn("severityBadge", src, "缺 severity 徽章渲染")
        self.assertIn("finding_impact", src, "发现流未用 severity 数据面")

    def test_entries_clickable_to_evidence_anchor(self):
        src = _src("index.html")
        self.assertIn('"/evidence#f=" + ', src,
                      "发现条目未按 /evidence#f=<发现号> 锚定跳转")

    def test_evidence_page_anchors_findings(self):
        src = _src("evidence.html")
        self.assertIn('"f-" + c.linked_finding', src,
                     "证据卡未铸 f=<发现号> 锚点")
        self.assertIn("scrollIntoView", src, "缺锚点滚动定位")
        self.assertIn("hashchange", src, "锚定未响应 hash 变化")
        self.assertIn("linked_finding", src)


if __name__ == "__main__":
    unittest.main()
