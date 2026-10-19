# -*- coding: utf-8 -*-
"""T1 读面骨架登录测试(测试先行:先跑红,再实现跑绿)。

覆盖:
- GET /health 形状
- 错钥 401 {"error": "密钥不对"}
- 对钥 200 + HttpOnly 会话 cookie
- 空钥缺省:配置化允许通过并标注 demo 模式
- 会话过期/无效 token 单元逻辑

运行: python3 -m unittest tests.readface.test_auth -v
"""
import hashlib
import os
import time
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server.readface.main import app
from server.readface.routers import auth

REAL_KEY = "test-secret-123"


class ReadfaceAuthTests(unittest.TestCase):
    def setUp(self):
        # 每个用例独立:清空内存会话表,避免用例间串味
        auth._sessions.clear()
        self.client = TestClient(app)

    # ---- /health ----

    def test_health_returns_ok_shape(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "service": "graphled-readface"})

    # ---- 错钥 ----

    def test_wrong_key_gets_401_and_no_cookie(self):
        with mock.patch.dict(os.environ, {"TANYIN_OPERATOR_KEY": REAL_KEY}):
            resp = self.client.post("/api/auth/login", json={"key": "not-the-secret"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json(), {"error": "密钥不对"})
        self.assertNotIn("session", resp.cookies)

    # ---- 对钥 ----

    def test_correct_key_sets_httponly_session_cookie(self):
        with mock.patch.dict(os.environ, {"TANYIN_OPERATOR_KEY": REAL_KEY}):
            resp = self.client.post("/api/auth/login", json={"key": REAL_KEY})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("ok"))
        self.assertFalse(body.get("demo"), "真钥登录不得标 demo")
        cookie_header = resp.headers.get("set-cookie", "")
        self.assertIn("session=", cookie_header)
        self.assertIn("HttpOnly", cookie_header, "会话 cookie 必须 HttpOnly")
        self.assertIn("Max-Age=43200", cookie_header, "cookie 寿命应与 12h TTL 一致")

    # ---- 空钥缺省:demo 模式 ----

    def test_empty_operator_key_allows_through_as_demo(self):
        with mock.patch.dict(os.environ, {"TANYIN_OPERATOR_KEY": ""}):
            resp = self.client.post("/api/auth/login", json={"key": "anything"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("demo"), "空钥缺省应标注 demo 模式")
        self.assertIn("session", resp.cookies)

    def test_demo_mode_is_configurable_off(self):
        env = {"TANYIN_OPERATOR_KEY": "", "READFACE_ALLOW_DEMO": "0"}
        with mock.patch.dict(os.environ, env):
            resp = self.client.post("/api/auth/login", json={"key": "anything"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json(), {"error": "密钥不对"})

    # ---- 会话逻辑(单元) ----

    def test_token_is_sha256_of_key_plus_salt(self):
        self.assertEqual(
            auth.make_token("k", "s"),
            hashlib.sha256(b"ks").hexdigest(),
        )

    def test_session_ttl_is_12_hours(self):
        before = time.time()
        token = auth.create_session("k")
        after = time.time()
        expiry = auth._sessions[token]
        self.assertAlmostEqual(expiry, before + 12 * 60 * 60, delta=(after - before) + 1)

    def test_expired_session_is_invalid_and_cleared(self):
        token = auth.create_session("k")
        self.assertTrue(auth.session_valid(token))
        auth._sessions[token] = time.time() - 1  # 拨回过去模拟过期
        self.assertFalse(auth.session_valid(token))
        self.assertNotIn(token, auth._sessions, "过期会话应被清除")

    def test_unknown_or_missing_token_is_invalid(self):
        self.assertFalse(auth.session_valid("deadbeef"))
        self.assertFalse(auth.session_valid(None))
        self.assertFalse(auth.session_valid(""))


if __name__ == "__main__":
    unittest.main()
