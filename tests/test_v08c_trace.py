# -*- coding: utf-8 -*-
"""v0.8 Task C：trace 只读检索——红绿测试。

红=现状：cli/ledger 无 trace_search 模块，battles runner 日志 + timeline.tsv
没有只读检索面。契约（docs/superpowers/plans/2026-10-11-v08-artex-borrow.md Task C）：
- search() 仅 literal substring（禁 regex，防正则炸弹）；
- 命中行附上下文各 2 行（文件首尾自然裁齐）；
- last=N 只保留最近 N 条命中；scope=runner_logs|timeline|both；battle 过滤；
- battles_dir 路径注入（本测试用 tmp fixture）；绝不写任何文件。
"""
import hashlib
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))

from ledger import trace_search
from ledger.trace_search import search

B1_LOG = "\n".join([
    "boot engine v2.1",
    "load mission.txt",
    "probe start",
    "probe iface enum",
    "ERROR NEEDLE authz denied",
    "retry backoff 30s",
    "settle begin",
    "war done",
]) + "\n"

B1_RUNNER = "\n".join([
    "2026-09-28T09:00:00Z\tPHASE\tP0",
    "2026-09-28T09:00:01Z\tLAUNCH\tpid=11",
    "2026-09-28T09:05:00Z\tNEEDLE\tstall-restart",
    "2026-09-28T09:05:30Z\tRESTART\tpid=12",
    "2026-09-28T18:00:00Z\tEXIT\t0",
]) + "\n"

B1_OUT = "runner stdout a\nrunner stdout b\nrunner stdout c\n"

B1_TL = "\n".join([
    "ts1\tactor1\tP0\tgoal-add\t-\tgenesis\th0\t2",
    "ts2\tactor1\tP0\tscope-include\t-\th0\th1\t2",
    "ts3\tactor1\tP1\tNEEDLE finding-filed\t-\th1\th2\t2",
    "ts4\tactor1\tP5\tgate-exit\t-\th2\th3\t2",
]) + "\n"

B2_LOG = "\n".join([
    "NEEDLE at head",
    "second line",
    "third line",
    "tail line NEEDLE",
]) + "\n"

B2_TL = "\n".join([
    "ts1\ta\tP0\tgoal-add\t-\tg\th\t2",
    "ts2\ta\tP5\tNEEDLE gate-exit\t-\tg\th2\t2",
]) + "\n"

# battle-3：无 NEEDLE 的安静战 + 正则元字符/超长串的猎物行
B3_LOG = "\n".join([
    "quiet war",
    "no needle here",
    "all calm",
    "wild .* line",
    "paren ( open",
    "a" * 30 + "b",
    "pad " + "A" * 5000,
]) + "\n"

B3_TL = "ts1\ta\tP0\tgoal-add\t-\tg\th\t2\n"


class TestTraceSearch(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        self.root = os.path.join(self.d.name, "battles")
        for rel, text in [
            (os.path.join("battle-1", "opencode-run.log"), B1_LOG),
            (os.path.join("battle-1", "opencode-run.log.runner.tsv"), B1_RUNNER),
            (os.path.join("battle-1", "runner.out"), B1_OUT),
            (os.path.join("battle-1", "G-r1", "timeline.tsv"), B1_TL),
            (os.path.join("battle-2", "opencode-run.log"), B2_LOG),
            (os.path.join("battle-2", "G-r2", "timeline.tsv"), B2_TL),
            (os.path.join("battle-3", "opencode-run.log"), B3_LOG),
            (os.path.join("battle-3", "G-r3", "timeline.tsv"), B3_TL),
        ]:
            self._w(rel, text)

    def _w(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def _tree_digest(self):
        """整树指纹：relpath -> sha256(bytes)——只读铁律的断言基尺。"""
        out = {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames.sort()
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                with open(p, "rb") as f:
                    out[os.path.relpath(p, self.root)] = hashlib.sha256(f.read()).hexdigest()
        return out

    def test_runner_logs_hits_ordered_with_line_no(self):
        hits = search("NEEDLE", scope="runner_logs", battles_dir=self.root)
        self.assertEqual([(h["file"], h["line_no"]) for h in hits], [
            (os.path.join("battle-1", "opencode-run.log"), 5),
            (os.path.join("battle-1", "opencode-run.log.runner.tsv"), 3),
            (os.path.join("battle-2", "opencode-run.log"), 1),
            (os.path.join("battle-2", "opencode-run.log"), 4),
        ], "文件序+行序确定性输出")
        self.assertTrue(all(h["source"] == "runner_logs" for h in hits))
        self.assertTrue(all("NEEDLE" in h["line"] for h in hits))

    def test_context_two_lines_each_exact(self):
        hits = search("NEEDLE", scope="runner_logs", battle=1, battles_dir=self.root)
        self.assertEqual(len(hits), 2)
        h = hits[0]
        self.assertEqual(h["line"], "ERROR NEEDLE authz denied")
        self.assertEqual(h["before"], ["probe start", "probe iface enum"])
        self.assertEqual(h["after"], ["retry backoff 30s", "settle begin"])

    def test_context_trimmed_at_file_boundaries(self):
        hits = search("NEEDLE", scope="runner_logs", battle=2, battles_dir=self.root)
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["line_no"], 1)
        self.assertEqual(hits[0]["before"], [], "文件头：before 自然为空")
        self.assertEqual(hits[0]["after"], ["second line", "third line"])
        self.assertEqual(hits[1]["line_no"], 4)
        self.assertEqual(hits[1]["before"], ["second line", "third line"])
        self.assertEqual(hits[1]["after"], [], "文件尾：after 自然为空")

    def test_scope_filter(self):
        both = search("NEEDLE", scope="both", battles_dir=self.root)
        tl = search("NEEDLE", scope="timeline", battles_dir=self.root)
        rl = search("NEEDLE", scope="runner_logs", battles_dir=self.root)
        self.assertEqual(len(rl), 4)
        self.assertEqual(len(tl), 2)
        self.assertEqual(len(both), 6, "both = runner_logs + timeline 之并")
        self.assertEqual({h["source"] for h in tl}, {"timeline"})
        self.assertEqual({h["source"] for h in rl}, {"runner_logs"})
        self.assertTrue(all(h["file"].endswith("timeline.tsv") for h in tl))

    def test_battle_filter(self):
        h1 = search("NEEDLE", scope="both", battle=1, battles_dir=self.root)
        self.assertEqual([(x["file"], x["line_no"]) for x in h1], [
            (os.path.join("battle-1", "G-r1", "timeline.tsv"), 3),
            (os.path.join("battle-1", "opencode-run.log"), 5),
            (os.path.join("battle-1", "opencode-run.log.runner.tsv"), 3),
        ])
        for form in (2, "2", "battle-2"):
            h2 = search("NEEDLE", scope="both", battle=form, battles_dir=self.root)
            self.assertEqual(len(h2), 3, "battle 参数三种形态等价：%r" % (form,))
            self.assertTrue(all(x["file"].startswith("battle-2") for x in h2))
        self.assertEqual(search("NEEDLE", battle=99, battles_dir=self.root), [],
                         "不存在的战号：空结果不炸")

    def test_last_truncation(self):
        full = search("NEEDLE", scope="both", battles_dir=self.root)
        self.assertEqual(len(full), 6)
        self.assertEqual(search("NEEDLE", scope="both", last=2, battles_dir=self.root),
                         full[-2:], "last=2 保留最近 2 条")
        self.assertEqual(search("NEEDLE", scope="both", last=10, battles_dir=self.root),
                         full, "last 超过总数：不截断")
        self.assertEqual(search("NEEDLE", scope="both", last=0, battles_dir=self.root),
                         [], "last=0：空")

    def test_literal_substring_never_regex(self):
        # ".*" 若按正则=全匹配；字面量只命中含 ".*" 的那一行
        hits = search(".*", scope="runner_logs", battles_dir=self.root)
        self.assertEqual([(h["file"], h["line_no"]) for h in hits],
                         [(os.path.join("battle-3", "opencode-run.log"), 4)])
        # 裸 "(" 在正则引擎直接 sre 报错；字面量静默命中
        hits = search("(", scope="runner_logs", battles_dir=self.root)
        self.assertEqual([(h["file"], h["line_no"]) for h in hits],
                         [(os.path.join("battle-3", "opencode-run.log"), 5)])
        # 经典灾难回溯串：正则对 a^30b 指数爆炸；字面量=零命中即时返回
        t0 = time.time()
        self.assertEqual(search("(a+)+$", scope="runner_logs", battles_dir=self.root), [])
        self.assertLess(time.time() - t0, 5.0, "禁 regex：灾难回溯 pattern 必须即时返回")

    def test_long_pattern_safe(self):
        t0 = time.time()
        self.assertEqual(search("A" * 1000000, battles_dir=self.root), [],
                         "超长 pattern 无命中也不得超时/超内存")
        self.assertLess(time.time() - t0, 5.0)
        # 长而可命中的 pattern 照常工作
        hits = search("A" * 4000, scope="runner_logs", battles_dir=self.root)
        self.assertEqual([(h["file"], h["line_no"]) for h in hits],
                         [(os.path.join("battle-3", "opencode-run.log"), 7)])

    def test_match_all_pattern_completes(self):
        # 全匹配（空串=literal 语义的匹配一切）：逐行命中、快速完成
        t0 = time.time()
        hits = search("", battle=3, scope="runner_logs", battles_dir=self.root)
        self.assertEqual([h["line_no"] for h in hits], [1, 2, 3, 4, 5, 6, 7])
        self.assertLess(time.time() - t0, 5.0)

    def test_readonly_never_writes(self):
        before = self._tree_digest()
        search("NEEDLE", scope="both", battles_dir=self.root)
        search("", scope="both", last=3, battles_dir=self.root)
        search("A" * 1000000, scope="both", battles_dir=self.root)
        self.assertEqual(self._tree_digest(), before, "只读铁律：检索不得写/改/增任何文件")

    def test_default_battles_dir_env_override(self):
        with mock.patch.dict(os.environ, {"TANYIN_HOME": os.path.join(self.d.name, "th")}):
            self.assertEqual(trace_search.default_battles_dir(),
                             os.path.join(self.d.name, "th", "battles"))
        env = {k: v for k, v in os.environ.items() if k != "TANYIN_HOME"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(trace_search.default_battles_dir(),
                             os.path.join(os.path.expanduser("~"), ".tanyin", "battles"))

    def test_bad_args_raise(self):
        with self.assertRaises(ValueError):
            search("x", scope="regex", battles_dir=self.root)
        with self.assertRaises(TypeError):
            search("x", last="3", battles_dir=self.root)
        with self.assertRaises(ValueError):
            search("x", last=-1, battles_dir=self.root)
        with self.assertRaises(TypeError):
            search(b"bytes", battles_dir=self.root)

    def test_missing_battles_dir_returns_empty(self):
        self.assertEqual(search("NEEDLE", battles_dir=os.path.join(self.d.name, "nope")), [])


if __name__ == "__main__":
    unittest.main()
