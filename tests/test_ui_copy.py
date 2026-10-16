#!/usr/bin/env python3
"""copy-v09d 界面文案人话律——禁词钉 + 替词钉（用户钦定词典的测试面）。

范围: 观察面七页 HTML + status.js 的「标签区」:
  nav 链接文字 / h1-h6 / button / option / legend / 统计项名 / 说明段落
  —— 即静态源里 script/style/pre/code/textarea/template 之外的一切可见文本
  (本站为纯前端渲染,原始数据只经 pre/code 运行时注入,静态源没有数据本体,
  pre/code 天然豁免 = 数据不动律的测试面表达)。
status.js 无 HTML 结构: 剥掉注释后全文按标签区对待(该文件本身就是文案单源)。

禁词表(用户钦定,出现任何一项=红):
  九门 | 十边 | 账本 | 验链 | 召回 | 投影 | EV- | FD- | G-r\d | opencode-run
替词钉(词典定稿): 菜单=总览/动态/对话/测试覆盖/攻击路线/发现/战报;
  footer=「探隐 v0.9d · 本页数据全部来自战斗记录，只能看不能改」;
  PENDING→未开始; 门名去「门」字系; 重放态/格态中文人话标签。
"""
import os
import re
import unittest
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "..", "cli", "webui", "static")
PAGES = ("index.html", "activity.html", "session.html", "coverage.html",
         "graph.html", "evidence.html", "metrics.html")
ALL_FILES = PAGES + ("status.js",)

BANNED = re.compile(r"九门|十边|账本|验链|召回|投影|EV-|FD-|G-r\d|opencode-run")

SKIP_TAGS = ("script", "style", "pre", "code", "textarea", "template")

NAV_WORDS = {"总览", "动态", "对话", "测试覆盖", "攻击路线", "发现",
             "战报", "实验", "设置（占位）"}

H1_WORDS = {"index.html": "总览", "activity.html": "动态",
            "session.html": "对话", "coverage.html": "测试覆盖",
            "graph.html": "攻击路线", "evidence.html": "发现",
            "metrics.html": "战报"}

FOOTER_WANT = "探隐 v0.9d · 本页数据全部来自战斗记录，只能看不能改"


def _src(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


class _VisibleText(HTMLParser):
    """标签区文本收集器: 跳过 script/style/pre/code/textarea/template。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.chunks.append(data)


def _visible_text(src):
    p = _VisibleText()
    p.feed(src)
    p.close()
    return "\n".join(p.chunks)


def _js_no_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)      # 块注释
    src = re.sub(r"(^|[^:])//[^\n]*", r"\1", src)         # 行注释（避开 ://）
    return src


def _label_zone(name):
    src = _src(name)
    if name.endswith(".js"):
        return _js_no_comments(src)
    return _visible_text(src)


class TestBannedWords(unittest.TestCase):
    """禁词钉: 标签区出现禁词表任何一项 = 红。"""

    def test_no_banned_words_in_label_zones(self):
        for name in ALL_FILES:
            with self.subTest(page=name):
                m = BANNED.search(_label_zone(name))
                self.assertIsNone(
                    m, "%s 标签区出现禁词: %r" % (name, m and m.group(0)))


class TestMenuDictionary(unittest.TestCase):
    """菜单词典钉: 七页侧栏链接文字全站同集=钦定菜单词。"""

    def test_nav_words_all_pages(self):
        for name in PAGES:
            with self.subTest(page=name):
                src = _src(name)
                m = re.search(r"<nav[^>]*>(.*?)</nav>", src, re.S)
                self.assertIsNotNone(m, name + " 缺 nav 块")
                words = {w.strip() for w in
                         re.findall(r">([^<>]+)</a>", m.group(1))}
                self.assertEqual(words, NAV_WORDS,
                                 "%s 菜单漂移: %s" % (name, words ^ NAV_WORDS))

    def test_h1_words(self):
        for name, want in H1_WORDS.items():
            with self.subTest(page=name):
                m = re.search(r"<h1>([^<]+)</h1>", _src(name))
                self.assertIsNotNone(m, name + " 缺 H1")
                self.assertEqual(m.group(1).strip(), want,
                                 "%s H1 应为「%s」" % (name, want))

    def test_footer_canonical_all_pages(self):
        for name in PAGES:
            with self.subTest(page=name):
                m = re.search(r"<footer>(.*?)</footer>", _src(name), re.S)
                self.assertIsNotNone(m, name + " 缺 footer")
                self.assertEqual(m.group(1).strip(), FOOTER_WANT,
                                 name + " footer 须为钦定文案")


class TestStatusJsPlainLabels(unittest.TestCase):
    """status.js 单源替词钉: 状态/门名/重放态/格态=人话中文。"""

    def test_gate_state_labels(self):
        js = _src("status.js")
        for key, want in (('"PASS"', "通过"), ('"FAIL"', "未通过"),
                          ('"PENDING"', "未开始")):
            m = re.search(r'%s:\s*\{\s*label:\s*"([^"]+)"' % key, js)
            self.assertIsNotNone(m, "GATE_STATE 缺 " + key)
            self.assertEqual(m.group(1), want,
                             "GATE_STATE %s 标签应为「%s」" % (key, want))

    def test_gate_names_no_gate_char(self):
        js = _src("status.js")
        m = re.search(r"TY\.NINE_GATES\s*=\s*\[(.*?)\];", js, re.S)
        self.assertIsNotNone(m, "status.js 缺 NINE_GATES 表")
        names = re.findall(r'name:\s*"([^"]+)"', m.group(1))
        self.assertEqual(len(names), 9, "九步须 9 个名字")
        for n in names:
            self.assertNotIn("门", n, "门名仍是「门」字系黑话: " + n)
            self.assertTrue(n.strip(), "门名不得为空")

    def test_replay_and_cell_labels(self):
        js = _src("status.js")
        replay = re.search(r"TY\.REPLAY_STATE\s*=\s*\{(.*?)\};",
                           js, re.S).group(1)
        for want in ("已复现", "未复现", "需人工", "环境差异", "未复测"):
            self.assertIn(want, replay, "REPLAY_STATE 缺人话标签 " + want)
        cell = re.search(r"TY\.CELL_STATE\s*=\s*\{(.*?)\};",
                         js, re.S).group(1)
        for want in ("已测", "已锁定", "未测"):
            self.assertIn(want, cell, "CELL_STATE 缺人话标签 " + want)
        self.assertNotIn("欠账", cell, "CELL_STATE 仍是欠账黑话")
        self.assertNotIn("冻结格", cell, "CELL_STATE 仍是冻结格黑话")


if __name__ == "__main__":
    unittest.main()
