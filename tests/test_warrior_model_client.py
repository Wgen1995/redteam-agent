# -*- coding: utf-8 -*-
"""战士运行时·模型客户端（W5 战士 MVP）——llmpool 判定核首次实战接线。

通道选择/错误分类/冷却/429 切道全经 cli.ledger.llmpool.LLMPoolRegistry
（283 行判定核的第一个真实消费者）；HTTP 面=stdlib urllib 直连 openai
兼容端点（judge_client 同款先例）。模型调用测试=本地假模型服务
（tests/test_warrior_fake_model.py，动态口），绝不真调外部 API。

跑法：python3 -m unittest tests.test_warrior_model_client -v
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import llmpool, llmpool_wire  # noqa: E402
from warrior import model_client  # noqa: E402
from tests.test_warrior_fake_model import FakeModelServer  # noqa: E402

DONE = '{"op":"done","reason":"枚举完成"}'


def chan(server, name):
    return {"name": name, "model": name, "base_url": server.base,
            "api_key": "stub-key"}


class TestModelClient(unittest.TestCase):
    def setUp(self):
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td)

    def _pool(self):
        return llmpool.LLMPoolRegistry(
            state_path=os.path.join(self.td, "pool.json"))

    def _client(self, channels, pool=None):
        return model_client.ModelClient(channels, pool or self._pool(),
                                        timeout=5.0)

    def test_success_reply_and_usage(self):
        self.srv.set_scripts({"m1": [{"content": DONE,
                                      "prompt_tokens": 321,
                                      "completion_tokens": 45}]})
        c = self._client([chan(self.srv, "m1")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.content, DONE)
        self.assertEqual(r.model, "m1")
        self.assertEqual(r.prompt_tokens, 321)
        self.assertEqual(r.completion_tokens, 45)
        self.assertEqual(len(r.attempts), 1)

    def test_usage_missing_falls_back_to_estimate(self):
        self.srv.set_scripts({"m1": [{"content": DONE,
                                      "with_usage": False}]})
        c = self._client([chan(self.srv, "m1")])
        r = c.chat([{"role": "user", "content": "abcdefghij"}])   # 10 chars
        self.assertTrue(r.ok)
        self.assertEqual(r.prompt_tokens, 4)      # ceil(10/3)
        self.assertGreater(r.completion_tokens, 0)

    def test_429_soft_failover_switches_channel(self):
        # m1 连吃三次 429（软计数阈值=3）→ 熔断进冷却 → pick 跳 m2 成功
        self.srv.set_scripts({
            "m1": [{"status": 429}, {"status": 429}, {"status": 429}],
            "m2": [{"content": DONE, "prompt_tokens": 10,
                    "completion_tokens": 5}]})
        c = self._client([chan(self.srv, "m1"), chan(self.srv, "m2")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.model, "m2")
        outcomes = [a["outcome"] for a in r.attempts]
        self.assertEqual(outcomes, ["http:429", "http:429", "http:429",
                                    "ok"])
        snap = c.pool.snapshot("m1")
        self.assertEqual(snap["state"], "cooling")

    def test_hard_401_immediate_failover(self):
        self.srv.set_scripts({
            "m1": [{"status": 401}],
            "m2": [{"content": DONE}]})
        c = self._client([chan(self.srv, "m1"), chan(self.srv, "m2")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertTrue(r.ok)
        self.assertEqual(r.model, "m2")
        self.assertEqual(c.pool.snapshot("m1")["state"], "tripped")

    def test_400_no_failover_fails_closed(self):
        self.srv.set_scripts({
            "m1": [{"status": 400}],
            "m2": [{"content": DONE}]})
        c = self._client([chan(self.srv, "m1"), chan(self.srv, "m2")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "http-error:400")
        self.assertEqual(len(r.attempts), 1, "no_failover 桶不切道")

    def test_all_channels_down_reports_exhausted(self):
        self.srv.set_scripts({
            "m1": [{"status": 401}],
            "m2": [{"status": 401}]})
        c = self._client([chan(self.srv, "m1"), chan(self.srv, "m2")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "all-channels-down")

    def test_network_error_soft_lane_then_next_channel(self):
        # m1 指向死口（连接拒绝=网络类软失败）→ 软计数 1 不熔断，但同轮内
        # 客户端继续尝试下一道 m2 成功
        self.srv.set_scripts({"m2": [{"content": DONE}]})
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        dead_port = s.getsockname()[1]
        s.close()
        dead = {"name": "m1", "model": "m1",
                "base_url": "http://127.0.0.1:%d/v1" % dead_port,
                "api_key": "k"}
        c = self._client([dead, chan(self.srv, "m2")])
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.model, "m2")
        self.assertIn("exc:", r.attempts[0]["outcome"])

    def test_wire_attach_pool_events_land_in_timeline(self):
        # llmpool_wire.attach 全链接线：goal 账本收 llm_failover 事件行
        gd = os.path.join(self.td, "G")
        shutil.copytree(FIX, gd)
        pool = llmpool_wire.attach(gd)
        self.srv.set_scripts({
            "m1": [{"status": 401}],
            "m2": [{"content": DONE}]})
        c = model_client.ModelClient([chan(self.srv, "m1"),
                                      chan(self.srv, "m2")], pool,
                                     timeout=5.0)
        r = c.chat([{"role": "user", "content": "ctx"}])
        self.assertTrue(r.ok)
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("llm_failover", tl)
        self.assertIn("event=trip", tl)
        self.assertIn("model=m1", tl)


if __name__ == "__main__":
    unittest.main()
