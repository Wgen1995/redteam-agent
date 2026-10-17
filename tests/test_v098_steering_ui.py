# -*- coding: utf-8 -*-
"""v0.9.8 方向盘批·二（企业级界面重造）——五页静态结构钉 + 向导活体冒烟。

参照实拆（docs/research/）:
- liveui/walk-csai-live.md §2.1B  批量队列 9 字段弹窗（工具审批/并发/调度/立即执行）
- manuals/usage-guide-zhulong.md §1.4+§2.0  向导式建任务/登录锁定
- liveui/2c-artex-visual-baseline.md  12 灰阶/图标/主按钮/密度
- manuals/usage-guide-multica.md + 活体 DOM  表单分区/36px 行密/输入件规格
- DeepSeek Harness 运行时（输入区形态/操作钮分色）

法律（同批一照旧）:
- 只改 cli/webui/static/** 界面层; server.py 路由与协议零触碰;
- 提交口径逐字节不变: POST /api/battle/new, JSON+X-Requested-With, 会话 cookie;
- 未接线字段一律 aria-disabled="true"+「即将支持」——不许假装能用;
- 零依赖（手绘内联 SVG）/18 色/4px 网格/五档字号/文案禁词表/菜单不变。

python3 -m unittest tests.test_v098_steering_ui
"""
import os
import re
import unittest
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
STATIC = os.path.join(CLI, "webui", "static")

BANNED = re.compile(r"九门|十边|账本|验链|投影|EV-|FD-|G-r\d|opencode-run")
GRID_PX = {"0", "4", "8", "12", "16", "20", "24", "32", "48"}
TIERS_PX = {"12", "13", "15", "20", "24"}
SPACING_RE = re.compile(
    r"(?<![-\w])(?:margin|padding|row-gap|column-gap|gap)"
    r"(?:-(?:top|right|bottom|left|block|inline|start|end))?\s*:\s*([^;{}]+)")


def _src(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


def _css(name):
    src = _src(name)
    return "".join(m.group(1)
                   for m in re.finditer(r"<style[^>]*>(.*?)</style>", src, re.S))


class _VisibleText(HTMLParser):
    """标签区可见文本（禁词面）：剥 script/style/pre/code/textarea/template。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "pre", "code", "textarea", "template"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "pre", "code", "textarea",
                   "template") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.chunks.append(data)


def _label_zone(name):
    p = _VisibleText()
    p.feed(_src(name))
    p.close()
    return "\n".join(p.chunks)


# ===========================================================================
# new.html —— 向导式四步（ZhuLong 骨架 + CSAI 字段密度）
# ===========================================================================

class TestNewWizardStructure(unittest.TestCase):
    """四步面板 + 步骤指示器 + 范围标签条 + 未接线禁用态 + 确认摘要。"""

    def test_four_step_panels_with_names(self):
        src = _src("new.html")
        steps = re.findall(
            r'<section[^>]*class="step[^"]*"[^>]*data-step="(\d)"', src)
        self.assertEqual(steps, ["1", "2", "3", "4"], "向导须四步面板 1-4")
        for kw in ("基本信息", "范围白名单", "预算与策略", "确认"):
            self.assertIn(kw, src, "步骤标题缺: " + kw)

    def test_step_indicator_circles_and_link(self):
        src = _src("new.html")
        self.assertIn('id="wiz-steps"', src, "缺步骤指示器容器")
        ol = re.search(r'<ol id="wiz-steps".*?</ol>', src, re.S)
        self.assertIsNotNone(ol, "指示器须为 ol")
        block = ol.group(0)
        self.assertEqual(len(re.findall(r'class="dot', block)), 4,
                         "指示器须 4 个圆点")
        for i in "1234":
            self.assertIn(">" + i + "<", block, "圆点须带序号 " + i)
        css = _css("new.html")
        self.assertIn(".wiz-line", css, "圆点间须有连线件")

    def test_only_first_step_initially_visible(self):
        src = _src("new.html")
        hidden = re.findall(
            r'<section[^>]*class="step[^"]*"[^>]*data-step="(\d)"[^>]*hidden',
            src)
        self.assertEqual(hidden, ["2", "3", "4"], "2-4 步初始须 hidden")

    def test_scope_tagstrip_and_live_parse(self):
        src = _src("new.html")
        self.assertIn('id="scope-tags"', src, "缺范围标签条容器")
        self.assertIn('id="scope-hint"', src, "缺红绿校验提示件")
        self.assertIn("scopeValid", src, "JS 须有格式校验函数")
        self.assertIn("scope-warning", src, "缺「无范围不开」醒目提示区")
        self.assertIn("无范围不开", _label_zone("new.html"), "醒目文案须可见")

    def test_dead_fields_cut_and_exec_now_live(self):
        """W1-T2 后法律：未接线摆设件（审批/并发/调度）砍净不留影；
        立即执行真启用（已接 launch 点火）——不许再挂「即将支持」假装。"""
        src = _src("new.html")
        for ctl in ("f-approval", "f-concurrency", "f-schedule"):
            self.assertNotIn('id="' + ctl + '"', src, ctl + " 已砍——不许留摆设")
        m = re.search(r'id="f-exec-now"[^>]*', src)
        self.assertIsNotNone(m, "缺立即执行控件")
        self.assertNotIn("disabled", m.group(0), "立即执行须真启用")
        self.assertNotIn("aria-disabled", m.group(0))
        self.assertNotIn("即将支持", src)
        self.assertNotIn("后端未接线", src)
        # 真接线证据：control 路由 + launch 动作入页
        self.assertIn("/api/battle/control", src)
        self.assertIn('"launch"', src)

    def test_budget_number_and_unit_assembly(self):
        src = _src("new.html")
        for ctl in ("f-budget-tokens", "f-budget-unit", "f-budget-reqs",
                    "f-budget-hours"):
            self.assertIn('id="' + ctl + '"', src, "缺预算控件 " + ctl)
        self.assertIn('id="f-budget-unit"', src)
        self.assertIn('";"', src.replace(" ", "") or src, "拼接须分号")

    def test_confirm_summary_echo_and_submit(self):
        src = _src("new.html")
        self.assertIn('id="sum-name"', src, "确认页须回显任务名称")
        self.assertIn('id="sum-scope"', src, "确认页须回显范围")
        self.assertIn('id="sum-budget"', src, "确认页须回显预算")
        self.assertIn('id="f-submit"', src, "提交钮须保留原 id")

    def test_submit_protocol_byte_identical(self):
        """提交口径逐字节钉：同 URL/方法/头/payload 四键。"""
        src = _src("new.html")
        self.assertIn('"/api/battle/new"', src)
        self.assertIn('"X-Requested-With": "XMLHttpRequest"', src)
        self.assertIn("name:", src)
        self.assertIn("scope:", src)
        self.assertIn("budget:", src)
        self.assertIn("note:", src)
        self.assertIn('r.status === 401', src, "401 跳登录语义须保留")

    def test_back_button_each_step(self):
        src = _src("new.html")
        self.assertIn('id="btn-prev"', src, "须有上一步钮（前一步可回改）")
        self.assertIn('id="btn-next"', src, "须有下一步钮")


# ===========================================================================
# login.html —— 品牌卡 + 显隐切换 + 锁定倒计时
# ===========================================================================

class TestLoginPageCraft(unittest.TestCase):

    def test_brand_mark_and_positioning(self):
        src = _src("login.html")
        self.assertIn("<svg", src, "须有品牌标（内联 SVG）")
        zone = _label_zone("login.html")
        self.assertIn("GraphLed", zone, "W1-T7 定名：品牌须 GraphLed")
        self.assertNotIn("探隐", zone)
        self.assertTrue(re.search(r"定位|只读|授权|观察", zone),
                        "须有一句定位文案")

    def test_password_peek_toggle(self):
        src = _src("login.html")
        self.assertIn('type="password"', src, "口令框初始须 password")
        self.assertIn('id="op-peek"', src, "缺显隐切换钮")
        self.assertIn("text", src, "JS 须切换为 text 显形")

    def test_lock_countdown_hook(self):
        src = _src("login.html")
        self.assertIn('id="lock-countdown"', src, "缺锁定倒计时件")
        self.assertIn("retry_after_s", src, "JS 须读 429 的 retry_after_s")
        self.assertIn("秒", src, "倒计时文案须含秒")


# ===========================================================================
# index.html —— 开战主按钮 + 审批列表行 + 空态
# ===========================================================================

class TestIndexUpgrades(unittest.TestCase):

    def test_start_button_icon(self):
        src = _src("index.html")
        btn = re.search(r'<a href="/new" id="start-btn">.*?</a>', src, re.S)
        self.assertIsNotNone(btn, "开战钮须保留 href=/new")
        self.assertIn("<svg", btn.group(0), "开战钮须带图标")

    def test_approval_rows_approve_reject_buttons(self):
        src = _src("index.html")
        self.assertIn('id="approval-card"', src)
        self.assertIn('id="approval-list"', src)
        self.assertIn("批准", src, "审批行须有批准钮")
        self.assertIn("拒绝", src, "审批行须有拒绝钮")
        self.assertIn("ap-ok", src)
        self.assertIn("ap-src", src, "行内须有来源位")

    def test_approval_empty_state(self):
        src = _src("index.html")
        self.assertIn("暂无待审", src, "空态文案「暂无待审」")
        self.assertIn("ap-empty", src, "空态插画件")

    def test_menu_unchanged(self):
        src = _src("index.html")
        for item in ("总览", "动态", "对话", "测试覆盖", "攻击路线", "发现",
                     "战报", "实验"):
            self.assertIn(item, src, "菜单项不得变: " + item)


# ===========================================================================
# session.html —— 介入框分色 + 急停二次确认层
# ===========================================================================

class TestSessionCockpit(unittest.TestCase):

    def test_stop_confirm_layer_exists(self):
        src = _src("session.html")
        self.assertIn('id="stop-confirm"', src, "缺急停二次确认层")
        self.assertIn('role="dialog"', src, "确认层须 dialog 语义")
        self.assertIn('id="stop-yes"', src, "缺确认急停钮")
        self.assertIn('id="stop-no"', src, "缺取消钮")
        self.assertNotIn("window.confirm", src,
                         "急停确认须页内弹层，不再用 window.confirm")

    def test_control_buttons_color_coding(self):
        css = _css("session.html")
        self.assertIn(".ctl-pause", css, "暂停钮样式类")
        pause = re.search(r"\.ctl-pause\s*\{[^}]*\}", css)
        self.assertIn("--warn", pause.group(0), "暂停=黄描边（warn 令牌）")
        stop = re.search(r"\.ctl-stop\s*\{[^}]*\}", css)
        self.assertIn("--bad", stop.group(0), "急停=红实心（bad 令牌）")
        self.assertIn("var(--bad)", stop.group(0))

    def test_send_button_present_with_controls(self):
        src = _src("session.html")
        for i in ("say-box", "say-send", "pause-btn", "resume-btn",
                  "stop-btn"):
            self.assertIn('id="' + i + '"', src, "操控件不得丢: " + i)


# ===========================================================================
# evidence.html —— 下载钮图标 + 悬停
# ===========================================================================

class TestEvidenceDownload(unittest.TestCase):

    def test_download_button_icon(self):
        src = _src("evidence.html")
        btn = re.search(r'<button id="report-dl".*?</button>', src, re.S)
        self.assertIsNotNone(btn)
        self.assertIn("<svg", btn.group(0), "下载钮须带图标")
        self.assertIn("#report-dl:hover", _css("evidence.html"),
                      "须有悬停态")


# ===========================================================================
# 工艺纪律扩展钉：new/login 两页入网（4px 网格/五档字号/18 色/禁词）
# ===========================================================================

class TestCraftDisciplineExtension(unittest.TestCase):
    """craft-v09d 五条硬验收扩到本批两新页（同 test_ui_craft 口径）。"""

    PAGES = ("new.html", "login.html")

    def test_spacing_grid(self):
        for name in self.PAGES:
            css = _css(name)
            for m in SPACING_RE.finditer(css):
                for tok in m.group(1).split():
                    tok = tok.strip(";")
                    if tok in ("0", "auto", "initial", "inherit"):
                        continue
                    mm = re.match(r"^([0-9.]+)px$", tok)
                    self.assertIsNotNone(
                        mm, "%s 间距非 px: %s" % (name, tok))
                    self.assertIn(str(int(round(float(mm.group(1))))),
                                  GRID_PX, "%s 间距档外: %s" % (name, tok))

    def test_font_size_tiers(self):
        for name in self.PAGES:
            css = _css(name)
            for m in re.finditer(r"font-size\s*:\s*([0-9.]+)px", css):
                self.assertIn(str(int(round(float(m.group(1))))), TIERS_PX,
                              "%s 字号档外: %s" % (name, m.group(0)))

    def test_banned_words_absent(self):
        for name in self.PAGES:
            m = BANNED.search(_label_zone(name))
            self.assertIsNone(m, "%s 禁词: %r" % (name, m and m.group(0)))

    def test_svg_no_fill_colors(self):
        """手绘图标零裸色（stroke 一律 currentColor/var）。"""
        for name in ("new.html", "login.html", "index.html",
                     "session.html", "evidence.html"):
            for m in re.finditer(r"<svg[^>]*>(.*?)</svg>", _src(name), re.S):
                inner = m.group(1)
                self.assertNotRegex(
                    inner, r'stroke="#|fill="#',
                    "%s SVG 图标不得用裸色值" % name)

    def test_font_stack_pingfang(self):
        for name in self.PAGES:
            self.assertIn("PingFang SC", _css(name), name + " 字族缺中文兜底")


# ===========================================================================
# 活体冒烟 —— 向导四步走通到提交（请求须打到 /api/battle/new；未登录 401 即证）
# ===========================================================================

class TestPlaywrightWizardSmoke(unittest.TestCase):

    def test_wizard_walk_hits_battle_new(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright 缺席 ENV-SKIP")
        from tests.test_v098_steering import (OP_KEY, SteeringBase,
                                              AUTH_DOC, AUTH_SHA)
        import os
        base = SteeringBase()
        base.setUp()
        self.addCleanup(base.td.cleanup)
        self.addCleanup(base.srv.shutdown)
        auth_path = os.path.join(base.td.name, "auth-wizard.pdf")
        with open(auth_path, "wb") as f:
            f.write(AUTH_DOC)
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(channel="chrome")
                except Exception as e:
                    self.skipTest("chrome 不可启动: %r" % e)
                page = browser.new_page()
                seen = {}
                def on_req(req):
                    if req.url.endswith("/api/battle/new"):
                        seen["url"] = req.url
                        seen["method"] = req.method
                        try:
                            seen["payload"] = req.post_data_json
                        except Exception:
                            seen["payload"] = None
                        seen["xrw"] = req.headers.get("x-requested-with")
                page.on("request", on_req)
                # B舰 P0 后：读面须会话——先经登录页拿 cookie 再进 /new
                page.goto("http://127.0.0.1:%d/login" % base.port)
                page.fill("#op-password", OP_KEY)
                page.click("#op-login")
                page.wait_for_url("**/new", timeout=8000)
                # 步1: 基本信息 + ①授权件上传 + ②窗口
                page.fill("#f-name", "冒烟向导战")
                page.fill("#f-note", "四步向导冒烟")
                page.set_input_files("#f-auth-file", auth_path)
                page.fill("#f-signer", "王安全（CISO）")
                page.fill("#f-valid-from", "2026-10-16T00:00:00Z")
                page.fill("#f-valid-until", "2026-10-23T00:00:00Z")
                page.wait_for_function(      # sha256 浏览器实算完才放行
                    "() => !document.getElementById('btn-next').disabled")
                page.click("#btn-next")
                # 步2: 范围白名单（标签条实时解析）+ ④联系人
                page.fill("#f-scope", "10.0.0.0/24\n*.smoke.example")
                page.wait_for_selector("#scope-tags .stag")
                page.fill("#f-contact", "138-0000-0000（王安全）")
                page.click("#btn-next")
                # 步3: 预算 + ⑥凭据来源
                page.fill("#f-budget-tokens", "1000")
                page.fill("#f-budget-reqs", "100")
                page.fill("#f-budget-hours", "10")
                page.fill("#f-cred-source", "客户提供测试账号")
                page.click("#btn-next")
                # 步4: 确认摘要 → ⑧法律勾选 → 提交（已登录=200 回执）
                page.wait_for_selector("#sum-name")
                page.check("#f-legal-ack")
                page.click("#f-submit")
                page.wait_for_selector("#new-result.ok", timeout=10000)
                self.assertEqual(seen.get("method"), "POST")
                self.assertTrue(seen["url"].endswith("/api/battle/new"))
                self.assertEqual(seen.get("xrw"), "XMLHttpRequest")
                pl = seen.get("payload") or {}
                self.assertEqual(pl.get("name"), "冒烟向导战")
                self.assertEqual(pl.get("scope"),
                                 ["10.0.0.0/24", "*.smoke.example"])
                self.assertEqual(pl.get("budget"), "1000;100;10")
                # 八问全量入 payload（①sha 前端实算值与原件一致）
                au = pl.get("auth") or {}
                self.assertEqual(au.get("sha256"), AUTH_SHA)
                self.assertTrue(au.get("content_b64"))
                self.assertEqual(au.get("signer"), "王安全（CISO）")
                self.assertEqual(pl.get("emergency_contact"),
                                 "138-0000-0000（王安全）")
                self.assertEqual(pl.get("cred_source"), "客户提供测试账号")
                self.assertIs(pl.get("legal_ack"), True)
                self.assertIn("battle-", page.inner_text("#new-result"))
                browser.close()
        finally:
            pass


if __name__ == "__main__":
    unittest.main()
