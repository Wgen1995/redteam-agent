# -*- coding: utf-8 -*-
"""批次 7 T17：Medium 收口两件（evals vacuous guard+impact 死分支）——裁决表全量落 b7 台账。

红=专家两例：
- evals 零指标文件/空目录 vacuous（零硬门 FAIL⇒soft rc=2 或 traceback，无 FAIL 判定
  输出）——guard 后 ⇒ rc=1 且输出含 vacuous；
- impact 死分支：write_cmds 单源枚举 {高,中,低}（write_cmds.py impact 门），
  cli/ledger 内一切对 impact 的 high/critical 比较=永假死分支——grep 判定零残留。
"""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
EVALS = os.path.join(ROOT, "cli", "tanyin-evals")


class TestEvalsVacuousGuard(unittest.TestCase):
    """M-收口①：零指标文件/空目录 ⇒ FAIL（输出含 vacuous 字样）rc=1。"""

    ZERO = '{"format_version":1,"metrics":[],"suites":{"static":[]}}'

    def _run(self, metrics_path):
        return subprocess.run(
            [sys.executable, EVALS, "run", "--metrics=" + metrics_path,
             "--suite=static", "--goal-dir=."],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=ROOT, timeout=300)

    def test_zero_metrics_file_fails_not_pass(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        mf = os.path.join(td.name, "metrics-zero.json")
        with open(mf, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.ZERO)
        r = self._run(mf)
        self.assertEqual(r.returncode, 1,
                         "红现状：零指标文件 rc=%d（vacuous 无硬门判定）\n%s"
                         % (r.returncode, r.stdout))
        self.assertIn("vacuous", r.stdout + r.stderr, "FAIL 输出须点名 vacuous")

    def test_missing_metrics_file_fails_not_crash(self):
        """空目录（指标文件缺）同面：rc=1+vacuous，非裸 traceback。"""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        r = self._run(os.path.join(td.name, "nope.json"))
        self.assertEqual(r.returncode, 1,
                         "红现状：指标文件缺=裸 traceback rc=%d" % r.returncode)
        self.assertIn("vacuous", r.stdout + r.stderr)


class TestImpactDeadBranchGone(unittest.TestCase):
    """M-收口②：impact 枚举={高,中,低}（write_cmds 单源），high/critical 比较=死分支。

    判定=cli/ledger 全目录 grep：行内同现 critical×(impact|severity) 且不引
    SEV2IMPACT 单源符号 ⇒ 死分支残留。ALLOW 白名单（计划：evals_metrics.py=
    impact 值域容忍面）——实勘该文件零命中行，白名单机制保留照计划原样。"""

    ALLOW = ("evals_metrics.py",)

    def test_no_dead_critical_branch_in_ledger(self):
        bad = []
        d = os.path.join(ROOT, "cli", "ledger")
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".py") or fn in self.ALLOW:
                continue
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if "critical" in line and ("impact" in line or "severity" in line) \
                            and "SEV2IMPACT" not in line:
                        bad.append("%s:%d %s" % (fn, i, line.strip()[:80]))
        self.assertEqual(bad, [],
                         "impact 枚举 {高,中,低} 下 critical 比较=死分支，必须清除:\n"
                         + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
