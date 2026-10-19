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


# ---------------------------------------------------------------------------
# T10 插话与转向: 意图三分类扩(steer/halt)+ /steer /halt /running + 桥 steer/halt。
# CLI 面实勘: tanyin-ledger 无 steer/stop 子命令——写面单源=cli/warrior/steer.py
# write_steer/write_stop(引擎 webui steer_reply 与 fleet supervisor 同款调用),
# 桥子进程内调该单源函数(goal 锁 append_tl_locked),事件形:
#   warrior-steer target=<warrior-id> text=<单行>  /  warrior-stop warrior=<id>
#   reason=<单行>(actor=总控 phase=P3);halt 另铸 deck-halt 留痕行
#   (fleet supervisor._signal fleet-stop 同律)。
# ---------------------------------------------------------------------------

import shutil                                      # noqa: E402

from ledger import core as ledger_core             # noqa: E402
from ledger import timeline as ledger_timeline     # noqa: E402
from ledger.schemas import TABLES                  # noqa: E402


def _chain(spec):
    """[(ts,actor,phase,event,revert_cmd)...] → 引擎真实接链 8 列行(test_overview 同律)。"""
    rows = []
    for ts, actor, phase, event, revert in spec:
        row, _prev = ledger_timeline.chained_row(rows, ts, actor, phase,
                                                 event, revert)
        rows.append(row)
    return rows


def _mk_goal(gd, tl_spec, tables=None):
    """微型 goal: 接链 timeline+若干净表(引擎 write_tsv 落盘,缺列补空)。"""
    os.makedirs(gd, exist_ok=True)
    ledger_core.write_tsv(os.path.join(gd, "timeline.tsv"), _chain(tl_spec))
    for tname, dict_rows in (tables or {}).items():
        cols = TABLES[tname]
        ledger_core.write_tsv(
            os.path.join(gd, tname),
            [[d.get(c, "") for c in cols] for d in dict_rows])


def _mk_runner(battle_dir, done=False):
    """runner 生命周期行: 已点火未完跑(LAUNCH 无 DONE)或已完跑(DONE)。"""
    lines = ["2026-10-20T09:00:00Z\tBOOT\tup",
             "2026-10-20T09:00:05Z\tLAUNCH\topencode"]
    if done:
        lines.append("2026-10-20T10:00:00Z\tDONE\tfinal_rc=0")
    with open(os.path.join(battle_dir, "opencode-run.log.runner.tsv"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# 在跑仗夹具 timeline: 一条立卡+两战士在编(w1 start/w2 heartbeat)
_TL_RUNNING = [
    ("2026-10-20T09:00:00Z", "op", "P0", "add-goal G-1 target=10.2.0.7", ""),
    ("2026-10-20T09:00:05Z", "runner", "P3",
     "warrior-start battle=battle-3 warrior=w1 pid=101 model=strong", ""),
    ("2026-10-20T09:00:06Z", "warrior:w2", "P3",
     "warrior-heartbeat warrior=w2 intent=INT-2", ""),
]


def _steer_intent(action="steer", target_intent=""):
    return json.dumps({"action": action, "target": "", "scope": [],
                       "budget_note": "", "questions": [],
                       "target_intent": target_intent}, ensure_ascii=False)


class TestIntentSteerHalt(SayBase):
    """/say 意图三分类扩: 开新仗(既有)/插话 steer/停 halt;target_intent 线索透传。"""

    def test_steer_words_status_steer_with_target_intent(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(
                _steer_intent(target_intent="跳过 10.2.0.9,重点 10.2.0.7"))):
            r = self.client.post("/api/chat/say",
                                 json={"text": "跳过 10.2.0.9,重点打 10.2.0.7"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "steer")
        self.assertEqual(body["intent"]["target_intent"],
                         "跳过 10.2.0.9,重点 10.2.0.7")
        self.assertNotIn("card", body)                 # 插话不产确认卡
        self.assertEqual(len(say._pending_cards), 0)

    def test_stop_words_status_halt(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(
                _steer_intent(action="halt"))):
            r = self.client.post("/api/chat/say", json={"text": "这场仗先停下"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "halt")
        self.assertNotIn("card", body)
        self.assertEqual(len(say._pending_cards), 0)

    def test_parse_intent_accepts_steer_halt_vocab(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(
                _steer_intent(target_intent="跳过 10.2.0.9"))):
            out = say.parse_intent("跳过 10.2.0.9")
        self.assertEqual(out["action"], "steer")
        self.assertEqual(out["target_intent"], "跳过 10.2.0.9")

    def test_unknown_action_still_rejected_no_guess(self):
        with mock.patch.object(say, "llm_chat", return_value=_ok_llm(
                _steer_intent(action="dance"))):
            r = self.client.post("/api/chat/say", json={"text": "跳舞"})
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())


def _steer_receipt(warriors=("w1", "w2")):
    return {"ok": True, "cmd": "steer", "battle": "battle-3",
            "goal_dir": "/tmp/x", "warriors": list(warriors),
            "timeline_row": 7, "text": "跳过 10.2.0.9", "intent": "",
            "note": "插话已入链"}


def _halt_receipt(stopped=("w1", "w2")):
    return {"ok": True, "cmd": "halt", "battle": "battle-3",
            "goal_dir": "/tmp/x", "stopped": list(stopped),
            "timeline_row": 9, "reason": "T10 验证",
            "note": "全停信号已入链"}


class TestSteerHaltApi(SayBase):
    """POST /api/chat/steer + /api/chat/halt: 校验面+桥调用参数断言+败路 502。"""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="t10-say-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.gd = os.path.join(self.home, "battles", "battle-3", "G-1")
        _mk_goal(self.gd, _TL_RUNNING)
        env = mock.patch.dict(os.environ, {"TANYIN_HOME": self.home})
        env.start()
        self.addCleanup(env.stop)
        goals = mock.patch.object(say, "_battle_goals",
                                  return_value=[("battle-3", self.gd)])
        goals.start()
        self.addCleanup(goals.stop)

    def _events(self):
        return [r[3] for r in ledger_timeline.read_rows(self.gd)]

    # ---- steer ----

    def test_steer_empty_text_422(self):
        r = self.client.post("/api/chat/steer",
                             json={"battle": "battle-3", "text": "  "})
        self.assertEqual(r.status_code, 422)
        self.assertIn("error", r.json())

    def test_steer_unknown_battle_404(self):
        with mock.patch.object(say, "_battle_goals", return_value=[]):
            r = self.client.post("/api/chat/steer",
                                 json={"battle": "battle-99", "text": "停"})
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.json())

    def test_steer_bridge_argv_asserted(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _steer_receipt()), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp) as run, \
                mock.patch.object(say, "_tl_has_row", return_value=True):
            r = self.client.post("/api/chat/steer", json={
                "battle": "battle-3", "text": "跳过 10.2.0.9,重点 10.2.0.7",
                "intent": "跳过 10.2.0.9"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["warriors"], ["w1", "w2"])   # 回执透传
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], sys.executable)
        self.assertIn("engine_bridge.py", argv[1])
        self.assertIn("steer", argv)
        i = argv.index("--battle")
        self.assertEqual(argv[i + 1], "battle-3")
        i = argv.index("--text")
        self.assertEqual(argv[i + 1], "跳过 10.2.0.9,重点 10.2.0.7")
        i = argv.index("--intent")
        self.assertEqual(argv[i + 1], "跳过 10.2.0.9")

    def test_steer_intent_flag_omitted_when_absent(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _steer_receipt(warriors=("w1",))), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp) as run, \
                mock.patch.object(say, "_tl_has_row", return_value=True):
            r = self.client.post("/api/chat/steer", json={
                "battle": "battle-3", "text": "重点 10.2.0.7"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("--intent", run.call_args[0][0])   # 无线索不带旗

    def test_steer_bridge_failure_502_honest(self):
        cp = subprocess.CompletedProcess([], 2, stdout="",
                                         stderr="boom: no battle")
        with mock.patch.object(say.subprocess, "run", return_value=cp):
            r = self.client.post("/api/chat/steer", json={
                "battle": "battle-3", "text": "停"})
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())
        self.assertNotIn("warriors", r.json())           # 不造假回执

    def test_steer_readback_mismatch_502(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _steer_receipt()), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp), \
                mock.patch.object(say, "_tl_has_row", return_value=False):
            r = self.client.post("/api/chat/steer", json={
                "battle": "battle-3", "text": "跳过 10.2.0.9"})
        self.assertEqual(r.status_code, 502)
        self.assertIn("读写不一致", r.json()["error"])

    def test_steer_end_to_end_real_bridge(self):
        r = self.client.post("/api/chat/steer", json={
            "battle": "battle-3", "text": "跳过 10.2.0.9,重点 10.2.0.7",
            "intent": "跳过 10.2.0.9"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["warriors"], ["w1", "w2"])
        evs = self._events()
        self.assertIn("warrior-steer target=w1 text=跳过 10.2.0.9,重点 10.2.0.7", evs)
        self.assertIn("warrior-steer target=w2 text=跳过 10.2.0.9,重点 10.2.0.7", evs)

    # ---- halt ----

    def test_halt_unknown_battle_404(self):
        with mock.patch.object(say, "_battle_goals", return_value=[]):
            r = self.client.post("/api/chat/halt",
                                 json={"battle": "battle-99"})
        self.assertEqual(r.status_code, 404)

    def test_halt_empty_battle_422(self):
        r = self.client.post("/api/chat/halt", json={"battle": " "})
        self.assertEqual(r.status_code, 422)

    def test_halt_bridge_argv_asserted(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _halt_receipt()), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp) as run, \
                mock.patch.object(say, "_tl_has_row", return_value=True):
            r = self.client.post("/api/chat/halt", json={
                "battle": "battle-3", "reason": "T10 验证"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["stopped"], ["w1", "w2"])
        argv = run.call_args[0][0]
        self.assertIn("halt", argv)
        i = argv.index("--battle")
        self.assertEqual(argv[i + 1], "battle-3")
        i = argv.index("--reason")
        self.assertEqual(argv[i + 1], "T10 验证")

    def test_halt_reason_flag_omitted_when_absent(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps(
            _halt_receipt(stopped=("w1",))), stderr="")
        with mock.patch.object(say.subprocess, "run",
                               return_value=cp) as run, \
                mock.patch.object(say, "_tl_has_row", return_value=True):
            r = self.client.post("/api/chat/halt", json={"battle": "battle-3"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("--reason", run.call_args[0][0])

    def test_halt_bridge_failure_502_honest(self):
        cp = subprocess.CompletedProcess([], 2, stdout="", stderr="boom")
        with mock.patch.object(say.subprocess, "run", return_value=cp):
            r = self.client.post("/api/chat/halt", json={"battle": "battle-3"})
        self.assertEqual(r.status_code, 502)
        self.assertIn("error", r.json())

    def test_halt_end_to_end_real_bridge(self):
        r = self.client.post("/api/chat/halt", json={
            "battle": "battle-3", "reason": "T10 活体验证"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["stopped"], ["w1", "w2"])
        evs = self._events()
        self.assertIn("warrior-stop warrior=w1 reason=T10 活体验证", evs)
        self.assertIn("warrior-stop warrior=w2 reason=T10 活体验证", evs)
        self.assertIn("deck-halt battle=battle-3 reason=T10 活体验证", evs)


class TestRunningDoc(SayBase):
    """GET /api/chat/running: 在跑仗条数据面(overview 执行中口径单源)。"""

    def setUp(self):
        super().setUp()
        self.home = tempfile.mkdtemp(prefix="t10-running-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        # battle-9: 已点火未完跑 → 执行中(条应显)
        b9 = os.path.join(self.home, "battles", "battle-9")
        _mk_goal(os.path.join(b9, "G-1"), _TL_RUNNING,
                 {"goals.tsv": [{"id": "G-1", "target": "10.2.0.9"}]})
        _mk_runner(b9)
        # battle-8: 已完跑(DONE final_rc=0)→非执行中(条不显)
        b8 = os.path.join(self.home, "battles", "battle-8")
        _mk_goal(os.path.join(b8, "G-1"), _TL_RUNNING,
                 {"goals.tsv": [{"id": "G-1", "target": "10.2.0.8"}]})
        _mk_runner(b8, done=True)

    def test_running_lists_running_battles_only(self):
        # battles_dir=battles 根(default_battles_dir 同位约定)
        doc = say.running_doc(battles_dir=os.path.join(self.home, "battles"))
        self.assertEqual([b["battle"] for b in doc["battles"]], ["battle-9"])
        row = doc["battles"][0]
        self.assertTrue(row["badge"].startswith("hsl("))   # 徽标同源派生
        self.assertIn("已点火", row["detail"])              # 态说明透传

    def test_endpoint_uses_env_home(self):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": self.home}):
            r = self.client.get("/api/chat/running")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual([b["battle"] for b in body["battles"]], ["battle-9"])

    def test_empty_root_no_battles_not_fake(self):
        empty = tempfile.mkdtemp(prefix="t10-empty-")
        self.addCleanup(shutil.rmtree, empty, True)
        doc = say.running_doc(battles_dir=empty)
        self.assertEqual(doc, {"battles": []})


class TestBridgeSteerHalt(unittest.TestCase):
    """engine_bridge steer/halt 真子进程(合成 TANYIN_HOME 真写——安全)。"""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="t10-bridge-home-")
        self.addCleanup(shutil.rmtree, self.home, True)
        _mk_goal(os.path.join(self.home, "battles", "battle-3", "G-1"),
                 _TL_RUNNING)
        # battle-4: 无战士在编(无 warrior-* 行)
        _mk_goal(os.path.join(self.home, "battles", "battle-4", "G-1"),
                 [("2026-10-20T09:00:00Z", "op", "P0",
                   "add-goal G-1 target=10.2.0.4", "")])

    def _run(self, *args):
        env = dict(os.environ, TANYIN_HOME=self.home)
        return subprocess.run(
            [sys.executable, BRIDGE] + list(args),
            capture_output=True, text=True, env=env, timeout=60)

    def _events(self, battle="battle-3"):
        gd = os.path.join(self.home, "battles", battle, "G-1")
        return [r[3] for r in ledger_timeline.read_rows(gd)]

    def _receipt(self, cp):
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        return json.loads(cp.stdout.strip().splitlines()[-1])

    def test_steer_fans_out_to_all_warriors(self):
        cp = self._run("steer", "--battle", "battle-3",
                       "--text", "跳过 10.2.0.9,重点 10.2.0.7",
                       "--intent", "跳过 10.2.0.9")
        receipt = self._receipt(cp)
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["cmd"], "steer")
        self.assertEqual(receipt["warriors"], ["w1", "w2"])
        self.assertEqual(receipt["timeline_row"], 5)   # 3 存量+2 新行
        self.assertEqual(receipt["intent"], "跳过 10.2.0.9")
        evs = self._events()
        self.assertIn("warrior-steer target=w1 text=跳过 10.2.0.9,重点 10.2.0.7", evs)
        self.assertIn("warrior-steer target=w2 text=跳过 10.2.0.9,重点 10.2.0.7", evs)

    def test_steer_no_warriors_defaults_w1(self):
        cp = self._run("steer", "--battle", "battle-4", "--text", "重点 10.2.0.4")
        receipt = self._receipt(cp)
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["warriors"], ["w1"])  # 引擎 webui 缺省同律
        self.assertIn("warrior-steer target=w1 text=重点 10.2.0.4",
                      self._events("battle-4"))

    def test_steer_missing_text_rc2(self):
        cp = self._run("steer", "--battle", "battle-3", "--text", " ")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("text", cp.stdout + cp.stderr)

    def test_steer_unknown_battle_rc2(self):
        cp = self._run("steer", "--battle", "battle-99", "--text", "停")
        self.assertEqual(cp.returncode, 2)

    def test_halt_stops_all_warriors_plus_audit_row(self):
        cp = self._run("halt", "--battle", "battle-3", "--reason", "T10 验证")
        receipt = self._receipt(cp)
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["cmd"], "halt")
        self.assertEqual(receipt["stopped"], ["w1", "w2"])
        evs = self._events()
        self.assertIn("warrior-stop warrior=w1 reason=T10 验证", evs)
        self.assertIn("warrior-stop warrior=w2 reason=T10 验证", evs)
        self.assertIn("deck-halt battle=battle-3 reason=T10 验证", evs)

    def test_halt_default_reason_when_omitted(self):
        cp = self._run("halt", "--battle", "battle-3")
        receipt = self._receipt(cp)
        self.assertTrue(receipt["ok"])
        self.assertIn("指挥台全停", receipt["reason"])
        self.assertIn("warrior-stop warrior=w1 reason=指挥台全停",
                      self._events())

    def test_halt_unknown_battle_rc2(self):
        cp = self._run("halt", "--battle", "battle-99")
        self.assertEqual(cp.returncode, 2)


if __name__ == "__main__":
    unittest.main()
