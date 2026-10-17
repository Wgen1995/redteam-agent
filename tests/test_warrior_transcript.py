# -*- coding: utf-8 -*-
"""战士运行时·原始对话存档（W5 战士 MVP · 质量律 R4）。

R4：transcript 目录独立于账本——账本=纪律事件（哈希链），transcript=全对话
留痕（我们的「LLM 录制」，ARTEX transcript 同构）。一意图一 jsonl 文件，
append-only，重启续写不断链；账本行绝不因 transcript 存在而增减。

跑法：python3 -m unittest tests.test_warrior_transcript -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys_path_cli = os.path.join(HERE, "..", "cli")
sys.path.insert(0, sys_path_cli)

from warrior import transcript  # noqa: E402


class TestTranscript(unittest.TestCase):
    def setUp(self):
        self.gd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.gd)

    def _lines(self, iid):
        p = os.path.join(self.gd, "transcripts", iid + ".jsonl")
        with open(p, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    def test_record_appends_jsonl_per_intent(self):
        t = transcript.Transcript(self.gd, battle="B-x", warrior="warrior:W-1")
        t.record("INT-1", "user", "ctx...", ts="2026-10-20T08:00:00Z",
                 model="m1", turn=1)
        t.record("INT-1", "assistant", '{"op":"done"}',
                 ts="2026-10-20T08:00:05Z", model="m1", turn=1,
                 usage={"prompt_tokens": 10, "completion_tokens": 5})
        rows = self._lines("INT-1")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["role"], "user")
        self.assertEqual(rows[0]["intent"], "INT-1")
        self.assertEqual(rows[0]["battle"], "B-x")
        self.assertEqual(rows[0]["warrior"], "warrior:W-1")
        self.assertEqual(rows[1]["usage"]["completion_tokens"], 5)
        self.assertEqual(rows[1]["model"], "m1")

    def test_one_file_per_intent_no_cross_mixing(self):
        t = transcript.Transcript(self.gd, battle="B-x", warrior="warrior:W-1")
        t.record("INT-a", "user", "a", ts="t1", model="m", turn=1)
        t.record("INT-b", "user", "b", ts="t2", model="m", turn=1)
        self.assertEqual(len(self._lines("INT-a")), 1)
        self.assertEqual(self._lines("b" if False else "INT-b")[0]["content"], "b")

    def test_append_only_survives_reopen(self):
        t = transcript.Transcript(self.gd, battle="B", warrior="warrior:W-1")
        t.record("INT-1", "user", "first", ts="t1", model="m", turn=1)
        t2 = transcript.Transcript(self.gd, battle="B", warrior="warrior:W-1")
        t2.record("INT-1", "assistant", "second", ts="t2", model="m", turn=1)
        self.assertEqual([r["content"] for r in self._lines("INT-1")],
                         ["first", "second"])

    def test_ledger_tables_untouched(self):
        t = transcript.Transcript(self.gd, battle="B", warrior="warrior:W-1")
        t.record("INT-1", "user", "x", ts="t", model="m", turn=1)
        self.assertEqual(os.listdir(self.gd), ["transcripts"],
                         "transcript 只写自家目录，账本表零触碰")

    def test_content_non_string_coerced_not_crash(self):
        t = transcript.Transcript(self.gd, battle="B", warrior="warrior:W-1")
        t.record("INT-1", "tool_result", {"rc": 0, "out": "xx"},
                 ts="t", model="local", turn=1)
        rows = self._lines("INT-1")
        self.assertEqual(rows[0]["content"], str({"rc": 0, "out": "xx"}))


if __name__ == "__main__":
    unittest.main()
