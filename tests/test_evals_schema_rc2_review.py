# -*- coding: utf-8 -*-
"""批次 7 评审收尾 I-3b（顺手 Minor b）：evals --metrics 缺 schema 键的合法 JSON
⇒ 裸 traceback 改 rc=2（用法域）。

红=专家反例：--metrics 指向合法 JSON 但缺 schema 键（无 format_version/缺指标
必填字段/顶层非对象）——load_metrics 抛 MetricsError/AttributeError 未接，
CLI 裸 traceback 退出（rc=1 且 stderr 有 Traceback，无用法提示）。
绿=在 vacuous 守卫之前拦截：文件在且 shape 不合 ⇒ stderr 单行「用法问题」+
rc=2（用法域，可修正重跑）；缺文件面维持 T17 vacuous rc=1 口径不变（零指标
文件/指标文件缺两例照旧）。
"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
EVALS = os.path.join(ROOT, "cli", "tanyin-evals")

# 缺 schema 键的合法 JSON 三形（评审反例+两工程化变体）
BAD_DOCS = '{"note": "合法 JSON 但缺 format_version/metrics schema 键"}'
BAD_ENTRY = ('{"format_version": 1, "suites": {"static": []},'
             ' "metrics": [{"id": "M99-x", "title": "缺 layer/gate/kind 等必填键"}]}')
BAD_ARRAY = '[1, 2]'


class TestEvalsSchemaUsageRc2(unittest.TestCase):
    def _write(self, text):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        mf = os.path.join(td.name, "metrics-bad.json")
        with open(mf, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return mf

    def _run(self, cmd, metrics_path):
        return subprocess.run(
            [sys.executable, EVALS, cmd, "--metrics=" + metrics_path,
             "--suite=static", "--goal-dir=."],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=ROOT, timeout=300)

    def _assert_usage_rc2(self, r, tag):
        self.assertEqual(r.returncode, 2,
                         "%s 须 rc=2 用法域（红态=裸 traceback）\n%s%s"
                         % (tag, r.stdout, r.stderr))
        self.assertNotIn("Traceback", r.stderr, "%s 不得裸 traceback" % tag)
        self.assertIn("用法", r.stdout + r.stderr, "%s 须给用法提示" % tag)

    def test_run_docs_without_schema_keys_exit_two(self):
        self._assert_usage_rc2(self._run("run", self._write(BAD_DOCS)), "run 缺 format_version")

    def test_run_entry_missing_required_keys_exit_two(self):
        self._assert_usage_rc2(self._run("run", self._write(BAD_ENTRY)), "run 指标缺必填键")

    def test_run_top_level_array_exit_two(self):
        self._assert_usage_rc2(self._run("run", self._write(BAD_ARRAY)), "run 顶层非对象")

    def test_list_missing_schema_keys_exit_two(self):
        self._assert_usage_rc2(self._run("list", self._write(BAD_DOCS)), "list 缺 format_version")


if __name__ == "__main__":
    unittest.main()
