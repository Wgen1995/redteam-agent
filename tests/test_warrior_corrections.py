# -*- coding: utf-8 -*-
"""战士运行时·工具生命周期自纠层（VulnClaw correction_layer 移植·战士化）。

移植哲学单源：不是规划器——只观察工具生命周期事件（前/后/批），存紧凑
事实/健康/时延/循环暗示，喂下一轮自纠信号；坏信号不炸循环。

API 最小 diff：既有面不动——loop 的 corrections 字符串列表与
ContextBuilder.build(corrections=[...]) 照旧；本层换掉轻量 in-memory 件，
工具事件（rc/out/err/时延）→ CorrectionSignal → ①即时 [diagnostic] 注记
（当轮指令结果面）②持存纠正信号（次轮上下文「上轮纠正信号」节）
③钉住事实（facts_extra → 「相关事实」节，参 R3 冷折叠）。

差异（自有战士运行时适配）：AgentState→进程内一意图一层（R1 零跨意图
继承）；事件源=guard 执行三元组 (rc,stdout,stderr)；无 evidence 面故
evidence_id 不移植；rc!=0 即判失败（guard 拒/环境不可用语义）。

跑法：python3 -m unittest tests.test_warrior_corrections -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "G-g1")
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import llmpool_wire  # noqa: E402
from tests.test_warrior_fake_model import FakeModelServer  # noqa: E402
from tools import install as tool_install  # noqa: E402
from warrior import corrections as corr_mod  # noqa: E402
from warrior import loop as wloop  # noqa: E402

W = "warrior:W-1"
TOOL = '{"op":"tool","card":"dig","args":["+short","A","shop.example"]}'
DONE = '{"op":"done","reason":"探测完成"}'


class TestCorrectionSignal(unittest.TestCase):
    def test_model_hint_joins_progress_and_hints(self):
        sig = corr_mod.CorrectionSignal(tool="dig", ok=True)
        sig.progress.append("HTTP status observed: 200")
        sig.hints.append("Diagnostic: dig is slow")
        joined = sig.model_hint()
        self.assertIn("HTTP status observed: 200", joined)
        self.assertIn("Diagnostic: dig is slow", joined)

    def test_content_digest_stable_and_short(self):
        self.assertEqual(corr_mod.content_digest("abc"),
                         corr_mod.content_digest("abc"))
        self.assertNotEqual(corr_mod.content_digest("abc"),
                            corr_mod.content_digest("abd"))
        self.assertRegex(corr_mod.content_digest("abc"), "^[0-9a-f]{16}$")


class TestHealthAndFailure(unittest.TestCase):
    def setUp(self):
        self.layer = corr_mod.CorrectionLayer()

    def test_ok_call_records_healthy_tool(self):
        sig = self.layer.after_tool_call("dig", ["A", "x.example"],
                                         ";; flags: qr rd ad",
                                         duration_ms=120)
        self.assertTrue(sig.ok)
        self.assertEqual(self.layer.health("dig").status, "healthy")

    def test_failure_marker_output_marks_not_ok(self):
        sig = self.layer.after_tool_call("curl", ["https://t.example"],
                                         "[!] query timed out")
        self.assertFalse(sig.ok)
        self.assertEqual(self.layer.health("curl").status, "degraded")
        self.assertTrue(any("failed or returned an error" in h
                            for h in self.layer.take_hints()))

    def test_nonzero_rc_marks_not_ok_with_error_text(self):
        sig = self.layer.after_tool_call("curl", [], "", rc=1,
                                         error="guard-reject: 界外")
        self.assertFalse(sig.ok)
        self.assertIn("guard-reject", self.layer.health("curl").last_error)

    def test_consecutive_failures_raise_degraded_pre_hint(self):
        for _ in range(2):
            self.layer.after_tool_call("dig", ["x"], "traceback ...")
        pre = self.layer.before_tool_call("dig", ["x"])
        self.assertIn("degraded", pre)
        self.assertIn("2 failure(s)", pre)

    def test_recovery_resets_health_and_pre_hint(self):
        self.layer.after_tool_call("dig", ["x1"], "[!] fail")
        self.layer.after_tool_call("dig", ["x2"], "[!] fail")
        self.layer.after_tool_call("dig", ["x3"], "ok answer")
        self.assertEqual(self.layer.health("dig").status, "healthy")
        self.assertEqual(self.layer.health("dig").consecutive_failures, 0)
        pre = self.layer.before_tool_call("dig", ["fresh-args"])
        self.assertNotIn("degraded", pre, "恢复后不再报降级预检")


class TestProgressAndPinnedFacts(unittest.TestCase):
    def setUp(self):
        self.layer = corr_mod.CorrectionLayer()

    def test_http_status_progress(self):
        sig = self.layer.after_tool_call(
            "curl", [], "HTTP/1.1 302\nLocation: /login")
        self.assertIn("HTTP status observed: 302", sig.progress)

    def test_url_progress_filters_dependency_doc_links(self):
        sig = self.layer.after_tool_call(
            "curl", [],
            "target https://admin.shop.example/login reachable; "
            "see https://urllib3.readthedocs.io/en/latest/")
        joined = " | ".join(sig.progress)
        self.assertIn("admin.shop.example/login", joined)
        self.assertNotIn("urllib3.readthedocs.io", joined)

    def test_flag_like_token_progress_and_pinned(self):
        sig = self.layer.after_tool_call("curl", [],
                                         "resp: flag{w5-corr-test} done")
        self.assertTrue(any("flag-like token observed: flag{w5-corr-test}"
                            in p for p in sig.progress))
        pinned = "\n".join(self.layer.pinned_fact_lines())
        self.assertIn("Observed flag-like token: flag{w5-corr-test}", pinned)

    def test_sql_source_pinned_with_semantic_hint(self):
        raw = ('$sql = "select * from users where id=" . $_GET["id"];'
               " -- scalar merge")
        self.layer.after_tool_call("cat", ["app.php"], raw)
        pinned = "\n".join(self.layer.pinned_fact_lines())
        self.assertIn("Source SQL:", pinned)
        self.assertTrue(any("SQL source is visible" in h
                            for h in self.layer.take_hints()))

    def test_form_and_input_facts_pinned(self):
        raw = ('<form method="post" action="/login">'
               '<input name="user" type="text"></form>')
        self.layer.after_tool_call("curl", ["https://t.example/login"], raw)
        pinned = "\n".join(self.layer.pinned_fact_lines())
        self.assertIn("HTML form: method=post action=/login", pinned)
        self.assertIn("HTML input: name=user type=text", pinned)

    def test_pinned_fact_lines_format_tool_pin_kind(self):
        self.layer.after_tool_call("curl", [],
                                   "found https://a.example/x")
        lines = self.layer.pinned_fact_lines()
        self.assertTrue(lines)
        self.assertTrue(all(" | tool-pin | " in l for l in lines),
                        str(lines))

    def test_pinned_facts_deduped_across_calls(self):
        for _ in range(3):
            self.layer.after_tool_call("curl", [],
                                       "found https://a.example/x")
        pinned = [l for l in self.layer.pinned_fact_lines()
                  if "a.example/x" in l]
        self.assertEqual(len(pinned), 1)


class TestLatencyRepetitionBatch(unittest.TestCase):
    def setUp(self):
        self.layer = corr_mod.CorrectionLayer()

    def test_slow_tool_latency_hint(self):
        sig = self.layer.after_tool_call("nmap", [], "ports open",
                                         duration_ms=16_000)
        self.assertTrue(any("took 16000ms" in h for h in sig.hints))
        self.assertTrue(any("latency is high" in h
                            for h in self.layer.take_hints()))

    def test_repetition_pre_hint_and_no_new_signal_post_hint(self):
        for _ in range(2):
            self.layer.after_tool_call("dig", ["+short", "A", "shop.example"],
                                       "ok-out dig 应答")
        pre = self.layer.before_tool_call("dig",
                                          ["+short", "A", "shop.example"])
        self.assertIn("already appeared 2 times recently", pre)
        self.assertTrue(any("no obvious new signal" in h
                            for h in self.layer.take_hints()))

    def test_batch_all_failed_hint(self):
        sigs = [self.layer.after_tool_call("dig", [], "[!] dead"),
                corr_mod.CorrectionSignal(tool="curl", ok=False)]
        self.assertIn("all tool calls in this batch failed",
                      self.layer.after_tool_batch(sigs))

    def test_batch_slow_tools_hint(self):
        sigs = [corr_mod.CorrectionSignal(tool="nmap", ok=True,
                                          duration_ms=20_000),
                corr_mod.CorrectionSignal(tool="dig", ok=True,
                                          duration_ms=1)]
        hint = self.layer.after_tool_batch(sigs)
        self.assertIn("slow tool(s) observed: nmap", hint)

    def test_take_hints_drains_and_dedupes(self):
        self.layer.after_tool_call("dig", [], "[!] timed out")
        self.layer.after_tool_call("dig", [], "[!] timed out")
        first = self.layer.take_hints()
        second = self.layer.take_hints()
        self.assertTrue(first)
        self.assertEqual(second, [], "take_hints=排空语义（次轮不重灌）")
        self.assertEqual(len(set(first)), len(first), "同文去重")


class _FixedSpawn(object):
    """固定 (rc,out,err) 的假执行器——不触网。"""

    def __init__(self, rc=0, out="", err=""):
        self.rc, self.out, self.err = rc, out, err

    def __call__(self, argv):
        return self.rc, self.out, self.err


class TestLoopIntegration(unittest.TestCase):
    """E2E：工具事件→自纠信号进次轮上下文（R1 组装面零 API 变更）。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp()
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.state = os.path.join(self.gd, "..",
                                  os.path.basename(self.gd) + "-cards.tsv")
        for n in ("curl", "dig"):
            ok, why = tool_install.install(n, "2026-10-18T10:00:00Z",
                                           state_path=self.state)
            self.assertTrue(ok, why)
        self.srv = FakeModelServer()
        self.addCleanup(self.srv.stop)

    def tearDown(self):
        shutil.rmtree(self.gd)

    def _run(self, scripts, spawn, **kw):
        self.srv.set_scripts(scripts)
        channels = [{"name": "m1", "model": "m1",
                     "base_url": self.srv.base, "api_key": "k"}]
        pool = llmpool_wire.attach(self.gd, env={})
        args = dict(goal_dir=self.gd, battle_name="B-x", channels=channels,
                    pool=pool, warrior_id=W, max_intents=3, max_turns=6,
                    token_cap=100000, tool_spawn=spawn,
                    tool_state_path=self.state, ctx_tokens=8000)
        args.update(kw)
        return wloop.WarriorLoop(**args).run()

    def _msgs(self, i=-1):
        return json.dumps(self.srv.requests[i]["messages"],
                          ensure_ascii=False)

    def test_failed_tool_feeds_next_turn_correction_section(self):
        spawn = _FixedSpawn(rc=1, err="[!] connection refused")
        rep = self._run({"m1": [{"content": TOOL}, {"content": DONE}]},
                        spawn)
        self.assertEqual(rep.status, "no-intents")
        self.assertIn("Diagnostic: dig failed or returned an error",
                      self._msgs(-1), "次轮上下文带上轮工具失败自纠信号")

    def test_pinned_url_injected_into_next_turn_facts(self):
        spawn = _FixedSpawn(out="admin panel at https://admin.shop.example/"
                                "login found")
        rep = self._run({"m1": [{"content": TOOL}, {"content": DONE}]},
                        spawn)
        self.assertEqual(rep.status, "no-intents")
        self.assertIn("Observed URL: https://admin.shop.example/login",
                      self._msgs(-1), "钉住事实进「相关事实」节")

    def test_repetition_pre_hint_visible_in_conversation(self):
        spawn = _FixedSpawn(out="ok-out dig 应答")
        rep = self._run({"m1": [{"content": TOOL}, {"content": TOOL},
                                {"content": TOOL}, {"content": DONE}]},
                        spawn)
        self.assertEqual(rep.status, "no-intents")
        all_msgs = json.dumps([r["messages"] for r in self.srv.requests],
                              ensure_ascii=False)
        self.assertIn("already appeared", all_msgs,
                      "重复调用预检注记上浮模型可见面")


if __name__ == "__main__":
    unittest.main()
