"""SPA 深链回退: /chat 刷新不 404;真文件直供; /api 不兜;目录穿越拒。"""
import os
import unittest
from fastapi.testclient import TestClient

from server.readface.main import _WEB_DIST, app


@unittest.skipUnless(_WEB_DIST.is_dir(), "需 web/dist 构建产物")
class SpaFallbackTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_deep_link_serves_index(self):
        r = self.client.get("/chat")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers["content-type"])
        self.assertIn(b"<div id=\"root\"></div>", r.content)

    def test_health_untouched(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_api_not_swallowed(self):
        self.assertEqual(self.client.get("/api/definitely-missing").status_code, 404)

    def test_traversal_rejected(self):
        # 穿越企图落到兜底 index.html,绝不泄仓外文件
        r = self.client.get("/../../etc/passwd")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<div id=\"root\"></div>", r.content)

    def test_real_asset_served(self):
        assets = _WEB_DIST / "assets"
        if not assets.is_dir():
            self.skipTest("无 assets 目录")
        some = next(assets.iterdir())
        r = self.client.get("/assets/" + some.name)
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
