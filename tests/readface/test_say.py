# -*- coding: utf-8 -*-
"""T6 说话开仗读面测试(测试先行:先跑红,再实现跑绿)。

覆盖(件A say.py + engine_bridge.py):
- 意图解析三型(mock LLM): 完整指令→confirm-ignite 确认卡(暂存);
  缺预算问询→status=ask 问回去不产卡; 闲聊→status=chat 直回不点火。
- LLM 链降级: 首钥 429 落次钥(轻客户端循环链逐钥); 首钥 401 同换;
  全链败→say 502 {"error"} 不造假; LLM 回非 JSON→502 不猜意图。
- 确认流: 批→engine_bridge 子进程 ignite(P0 一律 --dry-run,断言 CLI
  收到 --dry-run+目标); 拒→记录播报「已取消,目标保留」零子进程;
  未知 id/卡已用→404。
- 桥 dry-run 行为(真子进程,TANYIN_HOME 合成根): 回执 ok+dry_run+chain
  (battle 号=根上最大+1),battles 根纹丝不动(零写入); 缺 target→rc=2;
  不带 --dry-run→fail-closed(真点火 P0 未接线)。
- 读面零直写: say/chat/ask/拒全程无账本写(无子进程,除批确认走桥)。

运行(仓库根): PYTHONPATH=cli python3 -m unittest tests.readface.test_say -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server.readface.main import app
from server.readface.routers import say

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BRIDGE = os.path.join(REPO_ROOT, "server", "readface", "engine_bridge.py")

GOOD_ENVELOPE = json.dumps({
    "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
})


def _intent(action="ignite", target="", scope=None, budget_note="",
            questions=None):
    return json.dumps({"action": action, "target": target,
                       "scope": scope or [], "budget_note": budget_note,
                       "questions": questions or []}, ensure_ascii=False)


def _ok_llm(content):
    return {"ok": True, "content": content, "model": "mock",
            "attempts": [{"model": "mock", "outcome": "ok"}]}


class SayBase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        say._pending_cards.clear()


class TestIntentThreeShapes(SayBase):
    """意图解析三型: 完整指令/缺预算问询/闲聊不点火。"""

    def test_full_command_stages_confirm_card(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(_intent(
                target="demo.example.com", scope=["*.demo.example.com", "只读探测"],
                budget_note="50万 tokens,4 小时"))):
            r = self.client.post("/api/chat/say",
                                 json={"text": "对 demo.example.com 开仗,只读,50万 tokens 4小时"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "confirm")
        card = body["card"]
        self.assertEqual(card["kind"], "confirm-ignite")
        self.assertEqual(card["target"], "demo.example.com")
        self.assertEqual(card["scope"], ["*.demo.example.com", "只读探测"])
        self.assertEqual(card["budget"], "50万 tokens,4 小时")
        self.assertTrue(card["id"])
        self.assertIn("授权", card["auth_notice"])   # 授权提示一句
        # 卡已暂存: 同 id 可确认(下组用例走全链)

    def test_missing_budget_asks_back_no_card(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(_intent(
                target="demo.example.com",
                questions=["预算给多少(tokens/时长)?"]))):
            r = self.client.post("/api/chat/say",
                                 json={"text": "扫一下 demo.example.com"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ask")
        self.assertEqual(body["questions"], ["预算给多少(tokens/时长)?"])
        self.assertNotIn("card", body)
        self.assertEqual(len(say._pending_cards), 0)   # 未暂存任何卡

    def test_chat_smalltalk_direct_reply_no_card(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(_intent(
                action="chat"))):
            r = self.client.post("/api/chat/say", json={"text": "今天天气如何"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "chat")
        self.assertTrue(body["reply"])
        self.assertNotIn("card", body)
        self.assertEqual(len(say._pending_cards), 0)

    def test_empty_text_422(self):
        r = self.client.post("/api/chat/say", json={"text": "   "})
        self.assertEqual(r.status_code, 422)
        self.assertIn("error", r.json())


class TestLlmChainFailover(SayBase):
    """轻 LLM 客户端: 双钥链循环,429/401 换下一钥,全败回 error 不造假。"""

    CH = [{"name": "k1", "model": "m", "base_url": "http://x/v4",
           "api_key": "a1"},
          {"name": "k2", "model": "m", "base_url": "http://x/v4",
           "api_key": "a2"}]

    @staticmethod
    def _http_error(code):
        import urllib.error
        return urllib.error.HTTPError("http://x", code, "boom", None, None)

    def test_first_key_429_falls_to_second(self):
        replies = {"choices": [{"message": {"content": "ok-from-k2"},
                                "finish_reason": "stop"}]}
        with mock.patch.object(
                say, "_post_channel",
                side_effect=[self._http_error(429),
                             json.dumps(replies).encode("utf-8")]):
            out = say.llm_chat([{"role": "user", "content": "hi"}],
                               channels=self.CH)
        self.assertTrue(out["ok"])
        self.assertEqual(out["content"], "ok-from-k2")
        self.assertEqual([a["outcome"] for a in out["attempts"]],
                         ["http-429", "ok"])
        self.assertEqual([a["model"] for a in out["attempts"]],
                         ["k1", "k2"])           # 链序: 首钥败,次钥接

    def test_first_key_401_falls_to_second(self):
        replies = {"choices": [{"message": {"content": "ok"},
                                "finish_reason": "stop"}]}
        with mock.patch.object(
                say, "_post_channel",
                side_effect=[self._http_error(401),
                             json.dumps(replies).encode("utf-8")]):
            out = say.llm_chat([{"role": "user", "content": "hi"}],
                               channels=self.CH)
        self.assertTrue(out["ok"])
        self.assertEqual([a["outcome"] for a in out["attempts"]],
                         ["http-401", "ok"])

    def test_all_keys_fail_returns_error_no_fake(self):
        with mock.patch.object(
                say, "_post_channel",
                side_effect=self._http_error(429)):
            out = say.llm_chat([{"role": "user", "content": "hi"}],
                               channels=self.CH)
        self.assertFalse(out["ok"])
        self.assertIn("error", out)
        self.assertEqual(len(out["attempts"]), 2)   # 两钥都试过,留痕

    def test_say_endpoint_502_when_chain_dead(self):
        dead = {"ok": False, "error": "llm-chain-exhausted",
                "attempts": [{"model": "k1", "outcome": "http-429"},
                             {"model": "k2", "outcome": "http-429"}]}
        with mock.patch.object(say, "llm_chat", return_value=dead):
            r = self.client.post("/api/chat/say", json={"text": "开仗 demo.x"})
        self.assertEqual(r.status_code, 502)
        body = r.json()
        self.assertIn("error", body)
        self.assertNotIn("card", body)             # 不造假确认卡

    def test_llm_non_json_reply_502_no_guess(self):
        with mock.patch.object(say, "llm_chat",
                               return_value=_ok_llm("今天天气不错")):
            r = self.client.post("/api/chat/say", json={"text": "开仗 demo.x"})
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())


def _bridge_receipt(battle=7):
    return {"ok": True, "dry_run": True, "battle": battle,
            "chain": [], "note": "P0 dry-run 演练"}


class TestConfirmFlow(SayBase):
    """确认流: 批→桥子进程 --dry-run 点火; 拒→已取消; 坏 id→404。"""

    def _stage_card(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(_intent(
                target="demo.example.com", scope=["只读"],
                budget_note="50万 tokens"))):
            r = self.client.post("/api/chat/say", json={"text": "对 demo 开仗"})
        return r.json()["card"]

    def test_approve_calls_bridge_with_dry_run(self):
        card = self._stage_card()
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _bridge_receipt()), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp) as run:
            r = self.client.post("/api/chat/confirm",
                                 json={"id": card["id"], "approved": True})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["ignited"])
        self.assertTrue(body["dry_run"])
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], sys.executable)
        self.assertIn("engine_bridge.py", argv[1])
        self.assertIn("ignite", argv)
        self.assertIn("--dry-run", argv)            # P0 一律 dry-run
        i = argv.index("--target")
        self.assertEqual(argv[i + 1], "demo.example.com")
        # 卡一次用尽
        self.assertEqual(len(say._pending_cards), 0)

    def test_reject_records_cancel_no_subprocess(self):
        card = self._stage_card()
        with mock.patch.object(say.subprocess, "run") as run:
            r = self.client.post("/api/chat/confirm",
                                 json={"id": card["id"], "approved": False})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["cancelled"])
        self.assertIn("已取消", body["note"])
        self.assertIn("目标保留", body["note"])
        run.assert_not_called()                     # 拒=零子进程零写入

    def test_unknown_id_404(self):
        r = self.client.post("/api/chat/confirm",
                             json={"id": "nope", "approved": True})
        self.assertEqual(r.status_code, 404)

    def test_card_single_use(self):
        card = self._stage_card()
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _bridge_receipt()), stderr="")
        with mock.patch.object(say.subprocess, "run", return_value=cp):
            r1 = self.client.post("/api/chat/confirm",
                                  json={"id": card["id"], "approved": True})
            self.assertEqual(r1.status_code, 200)
        r2 = self.client.post("/api/chat/confirm",
                              json={"id": card["id"], "approved": True})
        self.assertEqual(r2.status_code, 404)       # 已用卡不复用

    def test_bridge_failure_502_honest(self):
        card = self._stage_card()
        cp = subprocess.CompletedProcess([], 2, stdout="",
                                         stderr="boom: no target")
        with mock.patch.object(say.subprocess, "run", return_value=cp):
            r = self.client.post("/api/chat/confirm",
                                 json={"id": card["id"], "approved": True})
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())
        self.assertNotIn("ignited", r.json())


class TestBridgeDryRun(unittest.TestCase):
    """engine_bridge ignite 真子进程(合成 TANYIN_HOME,零写入断言)。"""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="t6-bridge-home-")
        os.makedirs(os.path.join(self.home, "battles", "battle-3"))

    def _run(self, *args):
        env = dict(os.environ, TANYIN_HOME=self.home)
        return subprocess.run(
            [sys.executable, BRIDGE, "ignite"] + list(args),
            capture_output=True, text=True, env=env, timeout=60)

    def _tree(self):
        out = []
        for root, dirs, files in os.walk(self.home):
            for f in files:
                p = os.path.join(root, f)
                out.append((p, os.stat(p).st_mtime))
        return sorted(out)

    def test_dry_run_rehearses_chain_zero_writes(self):
        before = self._tree()
        cp = self._run("--target", "demo.example.com",
                       "--scope", "*.demo.example.com",
                       "--budget", "50万 tokens",
                       "--note", "只读", "--dry-run")
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        receipt = json.loads(cp.stdout.strip().splitlines()[-1])
        self.assertTrue(receipt["ok"])
        self.assertTrue(receipt["dry_run"])
        self.assertEqual(receipt["battle"], 4)      # 根上最大 3 → 4
        self.assertTrue(receipt["chain"])           # 演练链在回执里
        add_goal = receipt["chain"][0]
        self.assertIn("add-goal", add_goal)
        self.assertIn("demo.example.com", add_goal)
        self.assertTrue(any("add-scope" in step and "*.demo.example.com" in step
                            for step in receipt["chain"]))
        # 零写入: battles 根纹丝不动
        self.assertEqual(self._tree(), before)

    def test_missing_target_rc2(self):
        cp = self._run("--dry-run")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("target", cp.stdout + cp.stderr)

    def test_real_ignition_fail_closed(self):
        cp = self._run("--target", "demo.example.com")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("dry-run", cp.stdout + cp.stderr)   # 指路: P0 一律 dry-run


if __name__ == "__main__":
    unittest.main()
