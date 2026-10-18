# -*- coding: utf-8 -*-
"""⌘K/Ctrl-K 全局命令面板钉测（冒烟舰：组件 pages/_palette.js + 单页挂载）。

python3 -m unittest tests.test_webui_palette
律：纯 stdlib、3.9 兼容、前端零框架零 CDN；文案宪法#41（界面人话律——
「任务」不说「战」，内部代号不上屏；FD-/G-/EV- 是账本行址=产品标识，非内部代号）。

三层钉：
  ①组件纯逻辑层  node 直跑 _palette.js 的 CommonJS 导出（无 DOM 也须加载成功）：
    模糊匹配/行址解析/命令索引/分组/最近使用/最新任务与代域定位（≥12 例）。
  ②挂载结构层  techniques.html 冒烟挂载钉：守卫式加载器在场、仍只一外链
    （tests/test_webui_pagespec_techniques.py 单外链钉不破）、零 CDN、
    默认页面清单的每个文件真实存在。
  ③活体行为冒烟  playwright（浏览器缺席整类跳过不红）——真 Chromium 真页面
    真 ⌘K/Ctrl-K 键程：开合/键盘上下/回车执行/esc 关闭/模糊过滤/分组渲染/
    最近使用 localStorage/三类行址（FD-/G-/EV-）直达跳转。网络面用路由
    拦截喂桩（总装舰壳与 api_pages 挂载未落地——/api/v2/* 与页面路由由
    桩顶位，组件键盘与渲染行为全真）。
"""
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
PAGES_DIR = os.path.join(CLI, "webui", "static", "pages")
PALETTE = os.path.join(PAGES_DIR, "_palette.js")
SMOKE_PAGE = os.path.join(PAGES_DIR, "techniques.html")

# 宪法#41 禁词（界面人话律——各 pagespec 钉同源；行址前缀不属内部代号）
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战场", "战况")


def _node_eval(js):
    """node 直跑一段 JS（须 console.log(JSON.stringify(x)) 收尾）→ Python 对象。"""
    proc = subprocess.run(["node", "-e", js], capture_output=True,
                          text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("node 执行失败(%d): %s" % (proc.returncode, proc.stderr))
    out = proc.stdout.strip()
    if not out:
        raise AssertionError("node 无输出: %s" % proc.stderr)
    return json.loads(out.splitlines()[-1])


def _req():
    return "var P = require(%s);" % json.dumps(PALETTE)


# ═══════════════════════════ ① 组件纯逻辑层 ═══════════════════════════

class TestFuzzy(unittest.TestCase):
    def test_prefix_beats_subsequence(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.fuzzyScore('任务','任务列表'), P.fuzzyScore('任列','任务列表')]))")
        self.assertIsNotNone(r[0]); self.assertIsNotNone(r[1])
        self.assertGreater(r[0], r[1], "前缀命中须压过散字子序列")

    def test_case_insensitive_and_exact(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.fuzzyScore('TKS','tasks'), P.fuzzyScore('tasks','tasks'),"
            "P.fuzzyScore('TASKS','tasks')]))")
        self.assertIsNotNone(r[0], "大小写不敏感匹配")
        self.assertEqual(r[1], 1000, "全等=满分")
        self.assertEqual(r[2], 1000)

    def test_cjk_each_char_matches(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "P.fuzzyScore('技法','技法库')))")
        self.assertIsNotNone(r)
        self.assertGreater(r, 0)

    def test_miss_is_null_and_empty_query_zero(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.fuzzyScore('xyz','任务列表'), P.fuzzyScore('','x')]))")
        self.assertIsNone(r[0])
        self.assertEqual(r[1], 0, "空查询=0 分（全量基序）")


class TestParseAddress(unittest.TestCase):
    def test_fd_with_optional_goal(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.parseAddress('FD-2026-1'), P.parseAddress('fd-9@G-b2')]))")
        self.assertEqual(r[0], {"kind": "FD", "id": "FD-2026-1", "goal": ""})
        self.assertEqual(r[1], {"kind": "FD", "id": "FD-9", "goal": "G-b2"},
                         "小写行址归一为大写行址前缀")

    def test_g_and_ev_kinds(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.parseAddress('G-b2'), P.parseAddress('EV-7.1_2'),"
            " P.parseAddress('battle-2')]))")
        self.assertEqual(r[0]["kind"], "G")
        self.assertEqual(r[1]["kind"], "EV")
        self.assertIsNone(r[2], "battle-2 不是行址形（G- 前缀才认）")

    def test_plain_words_are_not_addresses(self):
        r = _node_eval(_req() + "console.log(JSON.stringify("
            "[P.parseAddress('任务列表'), P.parseAddress('  '),"
            "P.parseAddress(''), P.parseAddress('找一下FD-9')]))")
        for v in r:
            self.assertIsNone(v)


class TestIndexAndMatch(unittest.TestCase):
    def _cmds(self):
        return _node_eval(_req() + "console.log(JSON.stringify("
            "P.buildCommands(P.DEFAULT_PAGES)))")

    def test_index_shape_actions_then_pages(self):
        cmds = self._cmds()
        kinds = [c["kind"] for c in cmds]
        self.assertEqual(kinds[:4], ["action"] * 4, "动作在前（高频）")
        self.assertGreaterEqual(kinds.count("page"), 17,
                                 "默认页面清单至少覆盖已挂 17 页（含观察面/控制台页）")
        titles = [c["title"] for c in cmds if c["kind"] == "action"]
        self.assertEqual(titles, ["新建任务", "打开最新任务", "跳到最新发现", "打开报告中心"])

    def test_index_carries_absolute_routes(self):
        """href 绝对路由页（观察面/控制台）须直跳既有路由，不落兄弟相对名。"""
        r = _node_eval(_req() + "var c=P.buildCommands(P.DEFAULT_PAGES);"
            "console.log(JSON.stringify({"
            "console:c.find(x=>x.id==='page:console').url,"
            "session:c.find(x=>x.id==='page:session').url,"
            "tasks:c.find(x=>x.id==='page:tasks').url,"
            "evidence:c.find(x=>x.id==='page:evidence').url}))")
        self.assertEqual(r["console"], "/console")
        self.assertEqual(r["session"], "/session")
        self.assertEqual(r["evidence"], "/evidence")
        self.assertEqual(r["tasks"], "tasks.html",
                         "新页=兄弟页相对名（/p/ 路由下相对解析）")

    def test_merge_pages_shell_shape_wins(self):
        """壳形 {id,label,group,href}（nav.entries）：同 id 壳侧胜+绝对路由生效，
        新 id 追加；title/label 两种拼写都收。"""
        r = _node_eval(_req() +
            "var m=P.mergePages(P.DEFAULT_PAGES,"
            "[{id:'tasks',label:'任务列表（壳）',group:'作战',href:'/p/tasks'},"
            "{id:'ask',label:'问答',group:'管控',href:'/p/ask'}]);"
            "console.log(JSON.stringify({"
            "tasks:m.find(x=>x.id==='tasks'),"
            "ask:m.find(x=>x.id==='ask'),"
            "n:m.length}))")
        self.assertEqual(r["tasks"]["title"], "任务列表（壳）", "同 id 壳侧胜")
        self.assertEqual(r["tasks"]["href"], "/p/tasks")
        self.assertEqual(r["tasks"]["file"], "", "有 href 则兄弟相对名让位")
        self.assertEqual(r["ask"]["title"], "问答", "壳新页追加")
        self.assertEqual(r["ask"]["href"], "/p/ask")

    def test_match_orders_by_score(self):
        r = _node_eval(_req() + "var m=P.matchCommands('报告',P.buildCommands(P.DEFAULT_PAGES));"
            "console.log(JSON.stringify({top:m[0].cmd.id, top2:m[1].cmd.id,"
            "sorted:m.every((x,i)=>i===0||m[i-1].score>=x.score)}))")
        self.assertEqual(r["top"], "page:report-center", "标题前缀命中压过动作")
        self.assertTrue(r["sorted"], "按分降序稳定排")
        self.assertIn(r["top2"], ("act:open-report", "page:report-center"))

    def test_match_empty_query_returns_all_base_order(self):
        r = _node_eval(_req() +
            "var c=P.buildCommands(P.DEFAULT_PAGES);"
            "var m=P.matchCommands('',c);"
            "console.log(JSON.stringify({n:m.length, pages:c.filter(x=>x.kind==='page').length,"
            "all0:m.every(x=>x.score===0), first:m[0].cmd.id}))")
        self.assertEqual(r["n"], 4 + r["pages"], "空查询=全量（动作+页面）")
        self.assertTrue(r["all0"])
        self.assertEqual(r["first"], "act:new-task")

    def test_address_query_docks_lookup_first(self):
        r = _node_eval(_req() + "var m=P.matchCommands('FD-9@G-b2',P.buildCommands(P.DEFAULT_PAGES));"
            "console.log(JSON.stringify({kind:m[0].cmd.kind, title:m[0].cmd.title,"
            "url:m[0].cmd.url}))")
        self.assertEqual(r["kind"], "addr")
        self.assertEqual(r["title"], "直达发现 FD-9")
        self.assertEqual(r["url"], "finding-detail.html?id=FD-9&goal=G-b2")
        r2 = _node_eval(_req() + "var m=P.matchCommands('EV-77',P.buildCommands(P.DEFAULT_PAGES));"
            "console.log(JSON.stringify(m[0].cmd.title))")
        self.assertEqual(r2, "直达证据 EV-77")


class TestGroupAndRecent(unittest.TestCase):
    def _all(self):
        return _node_eval(_req() + "console.log(JSON.stringify("
            "P.matchCommands('', P.buildCommands(P.DEFAULT_PAGES))))")

    def test_group_fixed_order_and_recent_dedupe(self):
        matched = self._all()
        r = _node_eval(
            "var P=require(%s);" % json.dumps(PALETTE) +
            "var m=P.matchCommands('',P.buildCommands(P.DEFAULT_PAGES));"
            "var g=P.groupCommands(m,['page:tasks','act:new-task']);"
            "console.log(JSON.stringify({labels:g.map(x=>x.label),"
            "recent:g[0].items.map(x=>x.id),"
            "pages:g[g.length-1].items.map(x=>x.id).indexOf('page:tasks'),"
            "acts:g.filter(x=>x.label==='动作')[0].items.map(x=>x.id)}))")
        self.assertEqual(r["labels"], ["最近使用", "动作", "页面"], "固定组序")
        self.assertEqual(r["recent"], ["page:tasks", "act:new-task"], "最近使用按 recents 序")
        self.assertEqual(r["pages"], -1, "已在最近使用的项不在页面组重复出现")
        self.assertNotIn("act:new-task", r["acts"])

    def test_group_recent_absent_when_empty(self):
        r = _node_eval(
            "var P=require(%s);" % json.dumps(PALETTE) +
            "var g=P.groupCommands(P.matchCommands('',P.buildCommands(P.DEFAULT_PAGES)),[]);"
            "console.log(JSON.stringify(g.map(x=>x.label)))")
        self.assertEqual(r, ["动作", "页面"], "无最近使用=组不出现")

    def test_push_recent_move_to_front_cap(self):
        r = _node_eval(_req() + "console.log(JSON.stringify(["
            "P.pushRecent(['a','b','c'],'b'),"
            "P.pushRecent(['a','b'],'x',2),"
            "P.pushRecent([],'me')]))")
        self.assertEqual(r[0], ["b", "a", "c"], "重复使用置顶去重")
        self.assertEqual(r[1], ["x", "a"], "超帽截断")
        self.assertEqual(r[2], ["me"])


class TestResolvers(unittest.TestCase):
    BATTLES = ("var B=[{battle:'battle-1',n:1,goal:'G-a1',goal_id:'goal-1',"
               "updated:'2026-10-01T00:00:00Z'},"
               "{battle:'battle-2',n:2,goal:'G-b2',goal_id:'goal-2',"
               "updated:'2026-10-02T00:00:00Z'}];")

    def test_latest_battle_max_updated_tie_max_n(self):
        r = _node_eval(_req() + self.BATTLES +
            "console.log(JSON.stringify([P.latestBattle(B).n,"
            "P.latestBattle([{n:1,updated:'T'},{n:3,updated:'T'}]).n]))")
        self.assertEqual(r, [2, 3])

    def test_resolve_goal_addr_variants(self):
        r = _node_eval(_req() + self.BATTLES +
            "console.log(JSON.stringify(["
            "P.resolveGoalAddr(B,'G-a1').n, P.resolveGoalAddr(B,'g-b2').n,"
            "P.resolveGoalAddr(B,'goal-2').n, P.resolveGoalAddr(B,'battle-1').n,"
            "P.resolveGoalAddr(B,'2').n, P.resolveGoalAddr(B,'G-a').n,"
            "P.resolveGoalAddr(B,'G-a1-x'), P.resolveGoalAddr(B,'G-zz')]))")
        self.assertEqual(r[:5], [1, 2, 2, 1, 2], "代域/行id/任务号各形命中")
        self.assertEqual(r[5], 1, "≥3 字符前缀兜底（打得一半也能定位）")
        self.assertIsNone(r[6], "地址比代域长=非前缀，诚实不命中")
        self.assertIsNone(r[7])

    def test_ev_target_from_broadcast_rows(self):
        r = _node_eval(_req() +
            "var rows=[{evidence:[{id:'EV-77',finding:''},null]},"
            "{evidence:[{id:'EV-78',finding:'FD-9'}]}];"
            "console.log(JSON.stringify([P.evTarget(rows,'EV-78'),"
            "P.evTarget(rows,'EV-77'), P.evTarget([],'EV-78')]))")
        self.assertEqual(r[0], {"finding": "FD-9"})
        self.assertIsNone(r[1], "空挂接不算命中")
        self.assertIsNone(r[2])

    def test_url_builders(self):
        r = _node_eval(_req() + "console.log(JSON.stringify(["
            "P.findingUrl('FD-9','G-b2'), P.findingUrl('FD-9',''),"
            "P.sessionUrl(3), P.findingsUrl(12)]))")
        self.assertEqual(r, ["finding-detail.html?id=FD-9&goal=G-b2",
                             "finding-detail.html?id=FD-9",
                             "/session?battle=3", "/console/findings?battle=12"])


# ═══════════════════════════ ② 挂载结构层 ═══════════════════════════

class TestComponentStructure(unittest.TestCase):
    def _src(self):
        with open(PALETTE, encoding="utf-8") as f:
            return f.read()

    def test_palette_file_contract(self):
        src = self._src()
        self.assertIn("module.exports", src, "须可被 node require（纯逻辑测试单源）")
        self.assertIn("KeyK", src, "⌘K/Ctrl-K 键位单源")
        self.assertIn("tanyin.palette.recent.v1", src, "最近使用 storage 键钉")
        self.assertIn("window.__PALETTE_PAGES__", src, "总装舰壳页面清单注入位")
        self.assertNotIn("https://", src, "零 CDN")
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src, "宪法#41 禁词上屏: " + bad)

    def test_default_registry_files_exist_and_plain_words(self):
        src = self._src()
        files = re.findall(r'file: "([a-z0-9-]+\.html)"', src)
        self.assertGreaterEqual(len(files), 17, "默认清单至少覆盖当前已挂 17 页")
        for name in files:
            path = os.path.join(PAGES_DIR, name)
            self.assertTrue(os.path.isfile(path), "清单页不存在: " + name)
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src)


class TestSmokeMount(unittest.TestCase):
    def _src(self):
        with open(SMOKE_PAGE, encoding="utf-8") as f:
            return f.read()

    def test_loader_present_single_src_pin_intact(self):
        src = self._src()
        self.assertIn("window.__paletteLoaded", src, "守卫式加载器在场（幂等）")
        self.assertIn("_palette.js", src)
        self.assertEqual(src.count("<script src="), 1,
                         "仍只许共享壳一外链（动态注入不占坑）")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)
        self.assertGreaterEqual(len(src.splitlines()), 250)

    def test_palette_js_next_to_pages(self):
        self.assertTrue(os.path.isfile(PALETTE))
        self.assertTrue(os.path.basename(PALETTE).startswith("_"),
                        "下划线前缀=非页面件，不被页面挂载机制误收")


# ═══════════════════════════ ③ 活体行为冒烟 ═══════════════════════════

class TestLivePaletteSmoke(unittest.TestCase):
    """真 Chromium 真键程（playwright 缺席整类跳过不红）。

    网络面路由拦截喂桩：/api/v2/tasks.json 双任务桩、/api/v2/broadcast.json
    证据挂接桩、/api/v2/techniques.json 空卡桩（宿主页四态诚实降级）——
    组件键盘/渲染/跳转行为全真，与总装舰壳落地后的真实路由解耦。"""

    TASKS = {"battles": [
        {"battle": "battle-1", "n": 1, "goal": "G-a1", "goal_id": "goal-1",
         "name": "旧任务", "state": {}, "budget": {}, "findings": {},
         "created": "2026-10-01T00:00:00Z", "updated": "2026-10-01T00:00:00Z"},
        {"battle": "battle-2", "n": 2, "goal": "G-b2", "goal_id": "goal-2",
         "name": "新任务", "state": {}, "budget": {}, "findings": {},
         "created": "2026-10-02T00:00:00Z", "updated": "2026-10-02T00:00:00Z"}],
        "counts": {"battles": 2, "by_label": {}}, "states": [], "budget_warn_pct": 80}
    BROADCAST = {"rows": [
        {"evidence": [{"id": "EV-77", "finding": "FD-9"}]},
        {"evidence": []}]}
    TECH = {"cards": [], "counts": {"six_section": 0, "legacy": 0}}

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:                       # noqa: BLE001
            raise unittest.SkipTest("playwright 不可用: %s" % e)
        cls.pw = sync_playwright().start()
        try:
            try:
                cls.browser = cls.pw.chromium.launch()
            except Exception:                        # 缺内置二进制→系统 Chrome
                cls.browser = cls.pw.chromium.launch(channel="chrome")
        except Exception as e:                       # noqa: BLE001
            cls.pw.stop()
            raise unittest.SkipTest("Chrome 不可用: %s" % e)
        cls.page_errors = []

    @classmethod
    def tearDownClass(cls):
        for c in (getattr(cls, "browser", None), getattr(cls, "pw", None)):
            if c is not None:
                try:
                    c.close()
                except Exception:                    # noqa: BLE001
                    pass

    APP_JS_BARE = "/* 壳桩：无导航面（壳缺席轨） */"
    APP_JS_SHELL = (
        "var nav = (function () {"
        "  var entries = ["
        "    { id: 'tasks', group: '作战', label: '任务列表', href: '/p/tasks' },"
        "    { id: 'session', group: '作战', label: '任务详情', href: '/session' },"
        "    { id: 'ask', group: '管控', label: '问答', href: '/p/ask' }"
        "  ];"
        "  return { push: function () {}, toggle: function () {},"
        "           entries: function () { return entries.slice(); } };"
        "})();")

    def _mk_page(self, app_js=None):
        page = self.browser.new_page()
        self.page_errors = []
        page.on("pageerror", lambda e: self.page_errors.append(str(e)))
        page.on("console", lambda m: self.page_errors.append(m.text)
                if m.type == "error" else None)

        def _read(path):
            with open(path, "rb") as f:
                return f.read()

        def route(r):
            url = r.request.url
            if url.endswith("/static/app.js"):
                return r.fulfill(status=200, content_type="application/javascript",
                                 body=app_js if app_js is not None else self.APP_JS_BARE)
            if "/api/v2/tasks.json" in url:
                return r.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(self.TASKS, ensure_ascii=False))
            if "/api/v2/broadcast.json" in url:
                return r.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(self.BROADCAST, ensure_ascii=False))
            if "/api/v2/techniques.json" in url:
                return r.fulfill(status=200, content_type="application/json",
                                 body=json.dumps(self.TECH, ensure_ascii=False))
            if "_palette.js" in url:
                return r.fulfill(status=200,
                                 content_type="application/javascript; charset=utf-8",
                                 body=_read(PALETTE))
            if "/pages/techniques.html" in url:
                return r.fulfill(status=200, content_type="text/html; charset=utf-8",
                                 body=_read(SMOKE_PAGE))
            # 跳转落点（/session、/console/findings、兄弟页）——极简 html 桩
            return r.fulfill(status=200, content_type="text/html; charset=utf-8",
                             body="<!doctype html><title>ok</title>")

        page.route("**/*", route)
        page.goto("http://127.0.0.1/pages/techniques.html")
        page.wait_for_selector(".plk-root", state="attached", timeout=8000)
        return page

    def _open(self, page):
        page.keyboard.press("Control+k")
        page.wait_for_selector(".plk-root.on", timeout=3000)
        focused = page.evaluate(
            "document.activeElement && document.activeElement.classList.contains('plk-input')")
        self.assertTrue(focused, "开面板即聚焦输入框")

    def _first_selected_title(self, page):
        return page.locator(".plk-item.sel .t").inner_text()

    def test_toggle_open_close_and_focus(self):
        page = self._mk_page()
        self._open(page)
        page.keyboard.press("Escape")
        self.assertEqual(page.locator(".plk-root.on").count(), 0, "esc 关闭")
        page.keyboard.press("Control+k")
        page.wait_for_selector(".plk-root.on", timeout=3000)
        page.keyboard.press("Escape")
        self.assertEqual(page.locator(".plk-root.on").count(), 0)
        self.assertEqual(self.page_errors, [])

    def test_fuzzy_filter_groups_and_keyboard_nav(self):
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "任务")
        page.wait_for_selector(".plk-item", timeout=3000)
        labels = page.locator(".plk-g").all_inner_texts()
        self.assertIn("动作", labels)
        self.assertIn("页面", labels)
        titles = page.locator(".plk-item .t").all_inner_texts()
        self.assertIn("任务列表", titles)
        self.assertIn("新建任务", titles)
        first = page.locator(".plk-item.sel").get_attribute("data-i")
        page.keyboard.press("ArrowDown")
        second = page.locator(".plk-item.sel").get_attribute("data-i")
        self.assertNotEqual(first, second, "↓ 移动选择")
        page.keyboard.press("ArrowUp")
        self.assertEqual(page.locator(".plk-item.sel").get_attribute("data-i"), first,
                         "↑ 移回")
        page.fill(".plk-input", "技法库")
        page.wait_for_timeout(60)
        self.assertEqual(self._first_selected_title(page), "技法库")
        self.assertEqual(self.page_errors, [])

    def test_enter_navigates_page_and_recent_persisted(self):
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "设置")
        page.wait_for_timeout(60)
        self.assertEqual(self._first_selected_title(page), "设置")
        self.page_errors = []                      # 落点页是桩，只断言 URL
        page.keyboard.press("Enter")
        page.wait_for_url("**/pages/settings.html", timeout=5000)
        self.assertTrue(page.url.endswith("/pages/settings.html"))
        rec = page.evaluate("localStorage.getItem('tanyin.palette.recent.v1')")
        self.assertEqual(json.loads(rec), ["page:settings"], "最近使用落 localStorage")
        # 重开：最近使用组置顶
        page.goto("http://127.0.0.1/pages/techniques.html")
        page.wait_for_selector(".plk-root", state="attached", timeout=8000)
        self.page_errors = []
        page.keyboard.press("Control+k")
        page.wait_for_selector(".plk-root.on", timeout=3000)
        groups = page.locator(".plk-g").all_inner_texts()
        self.assertEqual(groups[0], "最近使用")
        self.assertEqual(page.locator(".plk-item .t").first.inner_text(), "设置")
        self.assertEqual(self.page_errors, [])

    def test_action_latest_battle_jumps(self):
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "打开最新任务")
        page.wait_for_timeout(60)
        self.assertEqual(self._first_selected_title(page), "打开最新任务")
        self.page_errors = []
        page.keyboard.press("Enter")
        page.wait_for_url("**/session?battle=2", timeout=5000)
        self.assertTrue(page.url.endswith("/session?battle=2"),
                        "最新任务=最近更新者（battle-2）")

    def test_address_g_fd_ev_direct(self):
        # G- 代域 → 任务详情
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "G-a1")
        page.wait_for_timeout(60)
        self.assertIn("直达任务", self._first_selected_title(page))
        self.assertEqual(page.locator(".plk-g").first.inner_text(), "查找")
        self.page_errors = []
        page.keyboard.press("Enter")
        page.wait_for_url("**/session?battle=1", timeout=5000)
        self.assertTrue(page.url.endswith("/session?battle=1"))

        # FD- 行址带所属任务代域 → 漏洞详情
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "FD-9@G-b2")
        page.wait_for_timeout(60)
        self.assertEqual(self._first_selected_title(page), "直达发现 FD-9")
        self.page_errors = []
        page.keyboard.press("Enter")
        page.wait_for_url("**/pages/finding-detail.html*", timeout=5000)
        self.assertIn("id=FD-9", page.url)
        self.assertIn("goal=G-b2", page.url)

        # EV- 行址 → 查播报挂接发现（桩：EV-77→FD-9，挂 battle-1 代域）
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "EV-77")
        page.wait_for_timeout(60)
        self.assertEqual(self._first_selected_title(page), "直达证据 EV-77")
        self.page_errors = []
        page.keyboard.press("Enter")
        page.wait_for_url("**/pages/finding-detail.html*", timeout=5000)
        self.assertIn("id=FD-9", page.url)

    def test_shell_present_hotkey_yield_and_registry(self):
        """总装壳在场（nav.entries/toggle）：裸 Ctrl+K 让位壳抽屉（面板不开），
        Ctrl+Shift+K 开面板；页面清单吃壳导航网（壳新页「问答」可查可跳）。"""
        page = self._mk_page(app_js=self.APP_JS_SHELL)
        page.keyboard.press("Control+k")
        page.wait_for_timeout(150)
        self.assertEqual(page.locator(".plk-root.on").count(), 0,
                         "裸 ⌘K 让位壳导航抽屉（键位协调）")
        page.keyboard.press("Control+Shift+k")
        page.wait_for_selector(".plk-root.on", timeout=3000)
        foot = page.locator(".plk-foot").inner_text()
        self.assertIn("⌘⇧K", foot, "壳在场时脚注改示 ⌘⇧K")
        page.fill(".plk-input", "问答")
        page.wait_for_timeout(80)
        titles = page.locator(".plk-item .t").all_inner_texts()
        self.assertIn("问答", titles, "壳 nav.entries 追加页可查")
        self.page_errors = []
        page.keyboard.press("Enter")
        page.wait_for_url("**/p/ask", timeout=5000)
        self.assertTrue(page.url.endswith("/p/ask"), "跳壳侧绝对路由")

    def test_no_match_honest_empty_state(self):
        page = self._mk_page()
        self._open(page)
        page.fill(".plk-input", "zzzz不存在的命令")
        page.wait_for_timeout(60)
        self.assertEqual(page.locator(".plk-item").count(), 0)
        self.assertIn("没有匹配", page.locator(".plk-empty").inner_text())
        self.assertEqual(self.page_errors, [])


if __name__ == "__main__":
    unittest.main()
