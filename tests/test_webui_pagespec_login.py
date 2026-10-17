# -*- coding: utf-8 -*-
"""T6·P1 登录页美化钉测（界面线施工计划 2026-10-18 T6 ①）。

python3 -m unittest tests.test_webui_pagespec_login
律：纯 stdlib、3.9 兼容、前端零框架零 CDN。
设计权威 docs/design/ui-spec-complete-v1.md §P1（唯一无会话可访问页）；
视觉=原型 panorama/graphled-console-prototype.html（12级灰阶+单强调色+mono数字）；
文案宪法#41（界面人话律）。

四态律（spec §P1）：空(首次,提示从启动日志取口令)/加载(按钮转圈)/错误(红字+输入
框红,不计细节)/正常(登录成功跳总览)；连续5败→锁定60s（429 retry_after_s 驱动
页内倒计时）。POST /login 窄门口径不变（JSON password+X-Requested-With）。

三层钉：
  ①页面层  static/login.html——四态结构钉+锁定倒计时钉+显隐切换钉+视觉令牌钉
           （灰阶阶标/强调色/mono）+零 CDN+宪法#41 禁词不上屏。
  ②行为层  真服动态口——GET /login 开放；错口令=401 人话错误体；连错 5 次=
           第 6 次尝试 429 且 retry_after_s≥1（锁定语义钉）；正口令=200+cookie。
  ③契约层  GraphLed 定名延续（test_webui_authform 既有钉不破）。
"""
import http.client
import json
import os
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
import sys  # noqa: E402

sys.path.insert(0, CLI)
from webui import server as srv_mod  # noqa: E402

PAGE = os.path.join(CLI, "webui", "static", "login.html")

ZONE_MARKS = (
    # 品牌区：Logo+产品名（GraphLed 定名钉延续）
    "<h1>GraphLed</h1>",
    # 口令输入（显示切换=peek 钮）+ 居中卡 360px（spec §P1 布局）
    'id="op-password"', 'id="op-peek"', "360px",
    # 四态：空(首次提示从启动日志取口令)/加载(按钮转圈)/错误(红字)/锁定倒计时
    'id="st-empty"', "启动日志",
    'class="spin"', "classList.add(\"loading\")",   # 加载态=按钮转圈（真机制）
    'id="op-msg"', "role=\"alert\"",
    'id="lock-countdown"', "aria-live",
    # 底部小字（spec §P1 原文）
    "本系统仅用于已授权的安全测试",
    # 锁定语义披露
    "锁定", "60 秒",
)
FETCH_MARKS = (
    "fetch(\"/login\"",
    "X-Requested-With",
    "JSON.stringify",
    "startLockdown",
    "retry_after_s",
    "/console",                     # 正常态=登录成功跳总览（spec §P1）
)
VISION_MARKS = (
    "--g0:#0a0b0d",                 # 原型灰阶 g0（12级灰阶令牌上页）
    "--acc:#3ddc97",                # 单强调色
    "--mono:",                      # mono 数字令牌
    "@keyframes spin",              # 加载态=按钮转圈动画
)
COPY_BANNED = ("看战况", "管战场", "作战室", "琥珀线", "一键链", "战况")


def page_src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


class TestLoginPageStructure(unittest.TestCase):
    """①页面层：四态+锁定倒计时+显隐切换+视觉令牌+零 CDN。"""

    def test_zones_and_states_present(self):
        src = page_src()
        for m in ZONE_MARKS:
            self.assertIn(m, src, "缺 " + m)

    def test_fetch_contract_marks(self):
        src = page_src()
        for m in FETCH_MARKS:
            self.assertIn(m, src, "缺 " + m)

    def test_vision_tokens_from_prototype(self):
        src = page_src()
        for m in VISION_MARKS:
            self.assertIn(m, src, "视觉令牌缺 " + m)

    def test_peek_toggle_and_lock_js_alive(self):
        src = page_src()
        self.assertIn("inp.type", src)                     # 显隐切换真实现
        self.assertIn("setInterval", src)                  # 倒计时真走秒
        self.assertIn("已锁定", src)                        # 人话锁定文案
        self.assertIn("锁定解除", src)

    def test_zero_framework_zero_cdn(self):
        src = page_src()
        self.assertEqual(src.count("<script src="), 0, "登录页零外链（无共享壳依赖）")
        self.assertNotIn("https://", src)

    def test_copy_banned_words_absent(self):
        src = page_src()
        for bad in COPY_BANNED:
            self.assertNotIn(bad, src, "宪法#41 禁词上屏: " + bad)

    def test_js_under_400_lines(self):
        src = page_src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 400)


class LoginHttpBase(unittest.TestCase):
    """起服（动态口，禁碰 8900）+HTTP 小助手。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.ledger = os.path.join(self.td.name, "G-bare")
        os.makedirs(self.ledger, exist_ok=True)
        self.key = "op-key-t6-login"
        self.srv = srv_mod.WebServer(("127.0.0.1", 0), srv_mod.Handler,
                                     ledger_dir=self.ledger,
                                     operator_key=self.key,
                                     battles_dir=os.path.join(self.td.name, "battles"))
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def post_login(self, password):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps({"password": password}).encode("utf-8")
        conn.request("POST", "/login", body=body, headers={
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "http://127.0.0.1:%d" % self.port})
        r = conn.getresponse()
        raw = r.read()
        hdrs = {"set-cookie": r.getheader("Set-Cookie") or ""}
        conn.close()
        try:
            j = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            j = {}
        return r.status, j, hdrs

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        r = conn.getresponse()
        raw = r.read()
        conn.close()
        return r.status, raw.decode("utf-8", "replace")


class TestLoginHttpContract(LoginHttpBase):
    """②行为层：错口令/5败锁定/429 倒计时供数/正口令 cookie。"""

    def test_login_page_open_and_branded(self):
        status, body = self.get("/login")
        self.assertEqual(status, 200)
        self.assertIn("GraphLed", body)
        self.assertIn("本系统仅用于已授权的安全测试", body)

    def test_wrong_password_401_human_error(self):
        status, j, _ = self.post_login("not-the-key")
        self.assertEqual(status, 401)
        self.assertIn("error", j)

    def test_five_failures_then_locked_429_with_retry_after(self):
        for _ in range(5):
            status, _, _ = self.post_login("bad")
            self.assertEqual(status, 401)
        status, j, _ = self.post_login("bad")            # 锁定期内第 6 次
        self.assertEqual(status, 429)
        self.assertGreaterEqual(int(j.get("retry_after_s", 0)), 1)
        self.assertIn("锁定", j["error"])

    def test_correct_password_gets_session_cookie(self):
        status, j, hdrs = self.post_login(self.key)
        self.assertEqual(status, 200)
        self.assertTrue(j.get("ok"))
        self.assertIn("tanyin_sess=", hdrs["set-cookie"])


if __name__ == "__main__":
    unittest.main()
