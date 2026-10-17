# -*- coding: utf-8 -*-
"""webui HTTP 测试共用件：起服后登录拿会话 cookie（B舰 P0 读面登录门后的夹具）。

用法（各 ServerBase.setUp）:
    self.srv = srv_mod.make_server(..., operator_key=webui_login.OP_KEY)
    self.port = self.srv.server_address[1]
    self.sid = webui_login.login(self.port)
    # GET 处: conn.request("GET", path, headers=webui_login.cookie(self.sid))
"""
import http.client
import json
import re

OP_KEY = "op-key-webui-tests"


def login(port, password=OP_KEY, timeout=5):
    """POST /login → 会话 cookie 值（失败=空串，调用方断言处自然爆）。"""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    body = json.dumps({"password": password}).encode("utf-8")
    conn.request("POST", "/login", body=body, headers={
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "http://127.0.0.1:%d" % port})
    resp = conn.getresponse()
    set_cookie = resp.getheader("Set-Cookie") or ""
    resp.read()
    conn.close()
    m = re.search(r"tanyin_sess=([^;]+)", set_cookie)
    return m.group(1) if m else ""


def cookie(sid):
    """GET 请求头字典（sid 空=空表——开放路由照常可用）。"""
    return {"Cookie": "tanyin_sess=" + sid} if sid else {}
