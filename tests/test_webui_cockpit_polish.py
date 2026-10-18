# -*- coding: utf-8 -*-
"""驾驶舱视觉/交互打磨舰——DOM 结构钉（GL-DS v1 六面同源+十件落点）。

python3 -m unittest tests.test_webui_cockpit_polish
律：纯 stdlib、零框架零 CDN 不破、页面 <2000 行；本测只读静态 HTML 断言
结构（军规十件①-⑩的 DOM 落点），既有 pagespec/vocab 门在姊妹测文件。
IA 保护（母舰军规）：首页四问/漏洞证据袋+复验/知识库三节的结构锚必须在场。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
STATIC = os.path.join(REPO, "cli", "webui", "static")

SIX = {
    "home": os.path.join(STATIC, "index.html"),
    "mission": os.path.join(STATIC, "pages", "mission.html"),
    "findings": os.path.join(STATIC, "pages", "findings.html"),
    "knowledge": os.path.join(STATIC, "pages", "knowledge.html"),
    "inbox": os.path.join(STATIC, "pages", "inbox.html"),
    "settings": os.path.join(STATIC, "pages", "settings.html"),
}
NAV_IDS = ("home", "mission", "findings", "knowledge", "inbox", "settings")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestDesignSystem(unittest.TestCase):
    """①-⑩ 十件落点的结构钉（六面全查）。"""

    def test_glds_canary_and_text_tiers(self):
        """①层级：GL-DS 标记+文字五档变量+字阶 13/14/16/20/24。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn("GL-DS v1", src, key)
            for var in ("--tx1", "--tx2", "--tx3", "--tx4", "--tx5"):
                self.assertIn(var + ":", src, key + " " + var)
            for fs in ("13px", "14px", "16px", "20px", "24px"):
                self.assertIn(fs, src, key + " " + fs)

    def test_color_semantics_single_source(self):
        """③色彩：状态四色+严重度五档变量+五档类名单源。"""
        for key, path in SIX.items():
            src = _read(path)
            for var in ("--ok:", "--warn:", "--dang:", "--info:",
                        "--sev-c:", "--sev-h:", "--sev-m:", "--sev-l:", "--sev-i:"):
                self.assertIn(var, src, key + " " + var)

    def test_severity_five_classes(self):
        """③严重度五档 class（危急/高/中/低/未知）在漏洞呈现面。"""
        for key in ("home", "mission", "findings"):
            src = _read(SIX[key])
            for cls in (".sev-c", ".sev-h", ".sev-m", ".sev-l", ".sev-i"):
                self.assertIn(cls + "{", src, key + " " + cls)
            self.assertIn('"sev-c"', src, key + " sevCls 五档映射")

    def test_six_components(self):
        """④组件：卡片/表格/徽章/进度条/空态/骨架屏六件同形。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn(".pane{", src, key + " 卡片")
            self.assertIn(".bdg{", src, key + " 徽章")
            self.assertIn('class="empty"', src, key + " 空态组件用法")
            self.assertIn(".skl", src, key + " 骨架屏")
            self.assertIn("@keyframes glm-sweep", src, key + " shimmer")
        for key in ("home", "mission", "findings"):
            src = _read(SIX[key])
            self.assertIn(".bar{", src, key + " 进度条")
        for key in ("mission", "knowledge", "settings"):
            src = _read(SIX[key])
            self.assertIn(".tbl{", src, key + " 表格")

    def test_empty_state_anatomy(self):
        """⑤空态：图标+标题(为什么空)+说明(下一步)——JS 生成或静态皆可。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertTrue("emptyBox(" in src or 'class="empty"' in src, key)
            self.assertIn('class="empty"', src, key)
            self.assertIn('class="t"', src, key)
            self.assertIn('class="d"', src, key)

    def test_skeleton_unified(self):
        """⑥加载态：shimmer 骨架屏六面同款（同一 keyframes 名）。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn('class="skl"', src, key)
            self.assertIn("glm-sweep", src, key)

    def test_hover_and_click_rows(self):
        """⑦交互：行 hover 高亮+可点行（漏洞页=证据袋卡 hover 展开）。"""
        for key in ("home", "mission"):
            src = _read(SIX[key])
            self.assertIn(".row.click:hover", src, key)
        for key in ("mission", "knowledge", "settings"):
            src = _read(SIX[key])
            self.assertIn(".tbl tbody tr:hover", src, key)
        self.assertIn(".fcard .hd:hover", _read(SIX["findings"]), "漏洞卡 hover")

    def test_findings_filters_and_pager(self):
        """⑦筛选器（状态/严重度/表面）+分页（25/页，>50 行）。"""
        src = _read(SIX["findings"])
        for anchor in ('data-f="verified"', 'data-f="queue"', 'data-f="suspect"',
                       'data-s="危急"', 'data-s="高"', 'data-s="中"', 'data-s="低"',
                       'id="f-surface"'):
            self.assertIn(anchor, src, anchor)
        self.assertIn("PAGE_SIZE = 25", src)
        self.assertIn('id="pg-prev"', src)
        self.assertIn('id="pg-next"', src)
        self.assertIn('id="pg-info"', src)

    def test_knowledge_pager(self):
        """⑦打法卡分页。"""
        src = _read(SIX["knowledge"])
        self.assertIn("PAGE_SIZE = 25", src)
        self.assertIn('id="pat-pager"', src)
        self.assertIn('id="pat-prev"', src)
        self.assertIn('id="pat-next"', src)

    def test_navigation_structure(self):
        """⑧导航：左侧固定栏+六面+当前页高亮+面包屑。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn('id="side"', src, key)
            self.assertIn('id="topbar"', src, key)
            self.assertIn('class="crumb"', src, key)
            for nid in NAV_IDS:
                self.assertIn('data-nav="' + nid + '"', src, key + " " + nid)
            # 当前页高亮：恰一个 .nav-i.on（本页自己）
            self.assertEqual(src.count('nav-i on'), 1, key + " 唯一高亮")
            self.assertIn('class="nav-i on" data-nav="' + key + '"', src, key)

    def test_responsive_breakpoints(self):
        """⑨响应：1280/1440/1920 三档（窄收 1279/1680 展宽+1024 折叠）。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn("@media(min-width:1680px)", src, key + " 1920 档")
            self.assertIn("@media(max-width:1279px)", src, key + " 1280 档")
            self.assertIn("@media(max-width:1024px)", src, key + " 折叠档")

    def test_details_typography_numbers_time(self):
        """⑩细节：tabular-nums+mono 相对时间+金额千分位。"""
        for key, path in SIX.items():
            src = _read(path)
            self.assertIn("font-variant-numeric:tabular-nums", src, key)
        for key in ("home", "mission", "inbox"):
            self.assertIn("function relTime", _read(SIX[key]), key + " 相对时间")
        self.assertIn("function fmtUsd", _read(SIX["home"]), "美元千分位")

    def test_pages_under_2000_lines(self):
        for key, path in SIX.items():
            n = len(_read(path).splitlines())
            self.assertLess(n, 2000, key + " 行数 " + str(n))

    def test_no_cdn_no_framework(self):
        for key, path in SIX.items():
            src = _read(path)
            self.assertNotIn("https://cdn", src, key)
            self.assertNotIn("http://cdn", src, key)
            self.assertNotIn("vue", src.lower().replace(
                "resumer", "").replace("value", ""), key + " 无框架")


class TestIaPreserved(unittest.TestCase):
    """母舰军规：IA 卖点不稀释——结构锚六面全在场。"""

    def test_home_four_questions(self):
        src = _read(SIX["home"])
        for anchor in ('id="q1"', 'id="q2"', 'id="q3"', 'id="q4"',
                       "/api/v2/cockpit.json", "/p/tasks"):
            self.assertIn(anchor, src, anchor)

    def test_mission_flow_and_tabs(self):
        src = _read(SIX["mission"])
        for anchor in ('id="flow"', 'data-t="overview"', 'data-t="map"',
                       'data-t="live"', 'data-t="vuln"', 'data-t="cost"',
                       'data-t="log"', "/api/v2/tasks.json"):
            self.assertIn(anchor, src, anchor)

    def test_findings_evidence_bag(self):
        src = _read(SIX["findings"])
        for anchor in ("证据袋", "上次验真", "待复验",
                       "/api/v2/cockpit-findings.json"):
            self.assertIn(anchor, src, anchor)

    def test_knowledge_three_sections(self):
        src = _read(SIX["knowledge"])
        for anchor in ("打法卡", "哨兵规则", "蒸馏",
                       "/api/v2/cockpit-knowledge.json"):
            self.assertIn(anchor, src, anchor)

    def test_inbox_three_kinds(self):
        src = _read(SIX["inbox"])
        for anchor in ("待审批", "求助", "批量", "/api/v2/cockpit-inbox.json"):
            self.assertIn(anchor, src, anchor)

    def test_settings_zones_intact(self):
        src = _read(SIX["settings"])
        for anchor in ('id="st-params"', 'id="st-scope"', 'id="st-history"',
                       'id="st-exempt"', 'id="st-form"', "'/api/v2/settings.json"):
            self.assertIn(anchor, src, anchor)

    def test_deep_links_survive(self):
        """深页 9 项在侧栏+页脚（旧页不删）。"""
        for key, path in SIX.items():
            src = _read(path)
            for slug in ("/p/tasks", "/p/retest", "/p/approval-center",
                         "/p/report-center", "/p/techniques"):
                self.assertIn(slug, src, key + " " + slug)


if __name__ == "__main__":
    unittest.main()
