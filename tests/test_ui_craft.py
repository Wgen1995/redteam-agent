# -*- coding: utf-8 -*-
"""v0.9d 视觉工艺批（craft-v09d）——治「整页等宽/间距杂值/颜色滥发」的五条硬验收。

python3 -m unittest tests.test_ui_craft
病历与治法（docs/design/ui-design-v1.md + 本批裁决）：
  ① 界面正文=系统无衬线栈（-apple-system/BlinkMacSystemFont/PingFang SC/...）；
     等宽字只许出现在数据块限定选择器（code/pre/类/ID 后代），body/html/*
     裸通用选择器带等宽字栈=红。
  ② 间距 4px 网格：margin/padding/gap（含长手 margin-top 等）只许
     0/auto/4/8/12/16/20/24/32/48 px；负值抵消处须行内 craft-wl 白名单注。
  ③ 颜色节食 ≤18：每页 CSS 原色值（<style> 块+内联 style）去重 ≤18；
     令牌区（:root 与深色镜像块）以外零裸色值——规则区一律 var()/currentColor。
  ④ 字号五档制：12/13/15/20/24 px，档外=红（font-size 与 font 简写都查）。
  ⑤ 字体栈含 PingFang SC（中文不落衬线兜底）。
  附加：阴影三档令牌 --shadow-1/2/3（卡/浮层/弹窗）双主题各定义一次，
     box-shadow 只许令牌引用或纯 var() 描边环（零裸色值）。
律：Python 3.9 纯 stdlib、只读扫描、TDD 先红后绿。
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "..", "cli", "webui", "static")
PAGES = ("index.html", "activity.html", "session.html", "coverage.html",
         "graph.html", "evidence.html", "metrics.html")

GRID_PX = {"0", "4", "8", "12", "16", "20", "24", "32", "48"}
TIERS_PX = {"12", "13", "15", "20", "24"}
MONO_WORDS = ("monospace", "menlo", "consolas", "courier", "mono")
WL = "craft-wl"                     # 行内白名单注（负 margin 抵消等豁免）

COLOR_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b"
    r"|rgba?\([^)]*\)|hsla?\([^)]*\)"
    r"|(?<![\w-])(?:white|black|red|blue|green|gray|grey|orange|yellow|"
    r"purple|pink|teal|cyan|brown|gold|silver)(?![\w-])")

SPACING_RE = re.compile(
    r"(?<![-\w])(?:margin|padding|row-gap|column-gap|gap)"
    r"(?:-(?:top|right|bottom|left|block|inline|start|end))?\s*:\s*([^;{}]+)")


def _src(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


def _css(name):
    """页内全部 <style> 块拼合（七页每页一块；JS 串不属 CSS 面）。"""
    src = _src(name)
    return "".join(m.group(1)
                   for m in re.finditer(r"<style[^>]*>(.*?)</style>", src, re.S))


def _rules(css):
    """扁平规则表 [(选择器, 声明区, 声明区起始偏移)]（本库 CSS 无嵌套块）。"""
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        out.append((m.group(1).strip(), m.group(2), m.start(2)))
    return out


def _token_spans(css):
    """令牌区=:root 首块 + 深色镜像块（裸色值唯一合法落点）。"""
    spans = []
    for pat in (r":root\s*\{.*?\}", r'html\[data-theme="dark"\]\s*\{.*?\}'):
        m = re.search(pat, css, re.S)
        if m:
            spans.append((m.start(), m.end()))
    return spans


def _line_of(css, pos):
    return css.count("\n", 0, pos)


def _declarations(body):
    """声明区 → [(属性, 值, 值起始偏移)]（只扫值区——选择器里的 #feed 等不算色值）。"""
    return [(m.group(1).lower(), m.group(2).strip(), m.start(2))
            for m in re.finditer(r"([\w-]+)\s*:\s*([^;]+)", body)]


def _font_sans_resolved(css):
    """--font-sans 令牌值（:root 定义）；缺席返回 None。"""
    m = re.search(r"--font-sans:\s*([^;]+)", css)
    return m.group(1).strip() if m else None


class TestFontCraft(unittest.TestCase):
    """①⑤ 正文字体律：系统无衬线栈+PingFang SC；等宽只给数据块。"""

    def test_body_font_is_system_sans_stack(self):
        for name in PAGES:
            css = _css(name)
            hit = None
            for sel, body, _ in _rules(css):
                toks = [t.strip() for t in sel.split(",")]
                if any(t in ("body", "html", "*") for t in toks):
                    for prop, val, _o in _declarations(body):
                        if prop == "font-family":
                            hit = (sel, val)
            self.assertIsNotNone(hit, name + " 缺 body/html 字族声明")
            stack = hit[1]
            if "var(" in stack:                       # 令牌引用 → 解析再验
                var = re.search(r"var\((--[\w-]+)\)", stack)
                self.assertIsNotNone(var, name + " body 字族 var 未知名")
                m = re.search(re.escape(var.group(1)) + r":\s*([^;]+)", css)
                self.assertIsNotNone(m, name + " body 字族令牌未定义")
                stack = m.group(1)
            low = stack.lower()
            for w in MONO_WORDS:
                self.assertNotIn(w, low,
                                 name + " body 字族混入等宽 " + stack)
            self.assertIn("-apple-system", stack,
                          name + " body 缺系统栈头 -apple-system")
            self.assertIn("PingFang SC", stack,
                          name + " body 缺 PingFang SC")

    def test_no_bare_universal_mono(self):
        for name in PAGES:
            for sel, body, _ in _rules(_css(name)):
                toks = [t.strip() for t in sel.split(",")]
                bare = [t for t in toks
                        if t in ("*", "body", "html") or t.endswith(" *")]
                if not bare:
                    continue
                for prop, val, _o in _declarations(body):
                    if prop != "font-family":
                        continue
                    low = val.lower()
                    for w in MONO_WORDS:
                        self.assertNotIn(
                            w, low,
                            "%s 裸选择器 %s 等宽字族越权" % (name, sel))

    def test_mono_confined_to_data_selectors(self):
        """等宽字族只许出现在带类/ID/元素限定的新代数选择器（数据块）。"""
        for name in PAGES:
            for sel, body, _ in _rules(_css(name)):
                for prop, val, _o in _declarations(body):
                    if prop != "font-family":
                        continue
                    if not any(w in val.lower() for w in MONO_WORDS):
                        continue
                    if "var(--font-mono)" not in val:
                        self.fail("%s 等宽须走 --font-mono 令牌: %s" % (name, val))
                    for tok in (t.strip() for t in sel.split(",")):
                        bare = re.fullmatch(r"[a-zA-Z]+|\*", tok)
                        self.assertIsNone(
                            bare, "%s 裸选择器 %s 不许等宽（数据块须限定）"
                            % (name, tok))

    def test_sans_and_mono_tokens_both_themes(self):
        for name in PAGES:
            css = _css(name)
            for var in ("--font-sans", "--font-mono"):
                self.assertGreaterEqual(css.count(var + ":"), 2,
                                        name + " " + var + " 浅/深未成对")
            m = re.search(r"--font-sans:\s*([^;]+);", css)
            self.assertIsNotNone(m, name + " 缺 --font-sans")
            self.assertIn("PingFang SC", m.group(1))       # ⑤


class TestSpacingGrid(unittest.TestCase):
    """② 间距 4px 网格：只许 0/auto/4/8/12/16/20/24/32/48 px。"""

    def test_spacing_on_grid_all_pages(self):
        for name in PAGES:
            css = _css(name)
            lines = css.split("\n")
            for m in SPACING_RE.finditer(css):
                if WL in lines[_line_of(css, m.start())]:
                    continue                            # 白名单行（负值抵消等）
                for tok in m.group(1).split():
                    tok = tok.strip(";")
                    if tok in ("0", "auto", "initial", "inherit"):
                        continue
                    mm = re.match(r"^(-?)([0-9.]+)px$", tok)
                    self.assertIsNotNone(
                        mm, "%s 间距非 px 网格值: %s (%s)"
                        % (name, tok, m.group(0).strip()))
                    if mm.group(1) == "-":
                        self.fail("%s 负间距未加 %s 注: %s"
                                  % (name, WL, m.group(0).strip()))
                    num = str(int(round(float(mm.group(2))))
                                 ) if mm.group(2) else "0"
                    self.assertIn(
                        num, GRID_PX,
                        "%s 间距档外值: %s" % (name, tok))


class TestColorDiet(unittest.TestCase):
    """③ 颜色节食：去重 ≤18；令牌区外零裸色值（只扫声明值区）。"""

    @staticmethod
    def _color_hits(css):
        """[(规则偏移, 值, [命中原色])]——选择器/注释不算色值。"""
        out = []
        for sel, body, off in _rules(css):
            for _prop, val, voff in _declarations(body):
                hits = COLOR_RE.findall(val)
                if hits:
                    out.append((off + voff, val, hits))
        return out

    def test_distinct_colors_le_18(self):
        for name in PAGES:
            css = _css(name)
            vals = set()
            for _off, _val, hits in self._color_hits(css):
                vals.update(v.lower() for v in hits)
            self.assertLessEqual(
                len(vals), 18,
                "%s 原色值去重 %d 种 > 18: %s" % (name, len(vals), sorted(vals)))

    def test_raw_colors_only_in_token_zone(self):
        for name in PAGES:
            css = _css(name)
            spans = _token_spans(css)
            self.assertGreaterEqual(len(spans), 2, name + " 缺令牌区双块")
            lines = css.split("\n")
            for off, val, hits in self._color_hits(css):
                if WL in lines[_line_of(css, off)]:
                    continue
                inside = any(s <= off < e for s, e in spans)
                self.assertTrue(
                    inside, "%s 令牌区外裸色值: %s (%s)"
                    % (name, hits, val))

    def test_inline_style_attrs_use_tokens(self):
        for name in PAGES:
            for m in re.finditer(r'style="([^"]*)"', _src(name)):
                hits = [h for h in COLOR_RE.findall(m.group(1))]
                self.assertEqual(
                    hits, [], "%s 内联 style 裸色值: %s" % (name, hits))


class TestFontSizeTiers(unittest.TestCase):
    """④ 字号五档制：12/13/15/20/24 px。"""

    def test_font_size_tiers(self):
        for name in PAGES:
            css = _css(name)
            for m in re.finditer(r"font-size\s*:\s*([0-9.]+)px", css):
                num = str(int(round(float(m.group(1)))))
                self.assertIn(num, TIERS_PX,
                              "%s 字号档外: %s" % (name, m.group(0)))
            for m in re.finditer(r"(?<![-\w])font\s*:\s*([^;{}]+)", css):
                head = m.group(1).split()[0] if m.group(1).split() else ""
                mm = re.match(r"^([0-9.]+)px", head)
                if mm:
                    self.assertIn(mm.group(1), TIERS_PX,
                                  "%s font 简写档外字号: %s" % (name, head))


class TestShadowTiers(unittest.TestCase):
    """阴影三档定死一次：双主题各一套令牌；box-shadow 零裸色值。"""

    def test_shadow_tokens_defined_both_themes(self):
        for name in PAGES:
            css = _css(name)
            for tok in ("--shadow-1", "--shadow-2", "--shadow-3"):
                self.assertGreaterEqual(css.count(tok + ":"), 2,
                                        name + " " + tok + " 浅/深未成对")
            self.assertGreaterEqual(css.count("var(--shadow-1)"), 1,
                                    name + " 卡片未用 --shadow-1")
            self.assertGreaterEqual(css.count("var(--shadow-2)"), 1,
                                    name + " 浮层未用 --shadow-2")

    def test_box_shadow_tokenized(self):
        for name in PAGES:
            for sel, body, _ in _rules(_css(name)):
                for prop, val, _o in _declarations(body):
                    if prop != "box-shadow":
                        continue
                    hits = COLOR_RE.findall(val)
                    self.assertEqual(
                        hits, [],
                        "%s box-shadow 裸色值: %s (%s)" % (name, val, sel))
                    self.assertIn("var(--", val,
                                  "%s box-shadow 未走令牌: %s" % (name, val))


if __name__ == "__main__":
    unittest.main()
