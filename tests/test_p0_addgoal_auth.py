# -*- coding: utf-8 -*-
"""P0 诚实性加固批（会诊⑤）：add-goal 授权校验前移。

旧：auth-sha256 只验 hex 格式，比对推迟到 P5 lint——b25 靠 LLM 诚实
halt 属侥幸依赖。新：授权书可达 ⇒ 实测 sha256 必须一致；不可达 ⇒
REJECT，唯 --allow-missing-auth=1（场景靶场虚拟授权书）显式豁免。"""
import hashlib, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
TS = "2026-09-24T10:00:00Z"


def call(gd, *args):
    return subprocess.run([sys.executable, CLI, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestAddGoalAuthHardening(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.auth = os.path.join(self.d, "AUTH.pdf")
        with open(self.auth, "wb") as f:
            f.write(b"authorization document\n")
        self.sha = hashlib.sha256(open(self.auth, "rb").read()).hexdigest()

    def tearDown(self):
        shutil.rmtree(self.d)

    def _args(self, sha=None, doc=None, extra=()):
        return ["--target=t.example", "--objective=授权测试",
                "--auth-doc=" + (doc or "AUTH.pdf"),
                "--auth-sha256=" + (sha or self.sha), "--signer=cso",
                "--valid-from=2026-09-01", "--valid-until=2026-09-30",
                "--budget=2M;50000;40", "--model-tier=strong", "--guard-tier=T3",
                "--timestamp=" + TS] + list(extra)

    def test_real_file_matching_sha_ok(self):
        r = call(self.d, "add-goal", *self._args())
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_real_file_wrong_sha_rejected(self):
        r = call(self.d, "add-goal", *self._args(sha="f" * 64))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("sha256", r.stderr + r.stdout)

    def test_missing_file_rejected_by_default(self):
        r = call(self.d, "add-goal", *self._args(doc="ghost.pdf"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("不在位", r.stderr + r.stdout)

    def test_missing_file_explicit_waiver_ok(self):
        r = call(self.d, "add-goal", *self._args(doc="ghost.pdf",
                                                 extra=("--allow-missing-auth=1",)))
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
