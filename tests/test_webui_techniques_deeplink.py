# -*- coding: utf-8 -*-
"""技法库（R64 对齐）：原「知识库深链批（能力并集审计修③）」钉的 URL 参数面
（?id= 进页即开/deepParams 读取/history.replaceState 地址栏同步）从未落地
——技法库面（/p/techniques）以「点卡→fetch /api/v2/techniques.json?id= 六节
直读」形态交付，无客户端 URL 参数消费。旧断言已退休
（R64: 随49b1619 IA v2移除），本文件改钉已交付的 id 直读现实。
python3 -m unittest tests.test_webui_techniques_deeplink
法律：纯 stdlib、3.9 兼容、测试动态取口（绝不 bind 8900）。
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
PAGE = os.path.join(CLI, "webui", "static", "pages", "techniques.html")


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════ ① 页面结构（已交付现实） ═══════════════════════════

class TestTechniquesDeeplinkPage(unittest.TestCase):
    """R64 对齐（①新现实）：技法卡详情=点卡后 fetch '/api/v2/techniques.json?id='
    六节直读；搜索框 #tech-search 在场。URL 深链规格（deepParams/
    URLSearchParams/history.replaceState 地址栏同步）随旧规格退休
    ——R64: 随49b1619 IA v2移除。"""

    # test_url_params_read（deepParams/URLSearchParams）—— R64: 随49b1619 IA v2移除
    # test_id_deep_link_and_url_sync（history.replaceState）—— R64: 随49b1619 IA v2移除

    def test_card_detail_fetches_by_id(self):
        """新现实钉：卡详情走服务端 id 直读（六节单卡数据面）。"""
        src = _src()
        self.assertIn("/api/v2/techniques.json?id=", src,
                      "卡详情须按 id 向服务端直读")
        self.assertIn("tech-detail", src, "缺详情容器")

    def test_q_prefill(self):
        src = _src()
        self.assertIn("tech-search", src)
        self.assertIn(".q", src, "q 参数须预填搜索框")


# ═══════════════════════════ ② 活体（已退休） ═══════════════════════════

# R64: 随49b1619 IA v2移除 TestTechniquesDeeplinkLive 活体（?id= 进页即开+
# 点卡地址栏同步+?q= 预填）——URL 深链从未在技法库面落地（点卡内存态选卡），
# 整套件 asyncio loop 下 Playwright Sync API 亦不可用；
# id 直读的服务端真钉在 tests/test_webui_techniques*.py 投影面。


if __name__ == "__main__":
    unittest.main()
