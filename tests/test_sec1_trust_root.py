# -*- coding: utf-8 -*-
"""SEC-1 舰 S1（2026-10-15 v0.9.6 执法面升权批）：信任根摘出。

依据 docs/superpowers/plans/2026-10-15-v096-enforcement.md SEC-1 舰节 +
docs/reviews/2026-10-15-direction-review/02-security-enforcement.md S1：
战士进程与执法面同 env——TANYIN_JUDGE_*/TANYIN_APPROVAL_KEY/TANYIN_VAULT_*
随 runner `env = dict(os.environ)` 全量泄给战士。

两面：
1. runner warrior_env 白名单：战士进程只继承必需面（PATH/HOME 等 + 非密
   TANYIN_HOME/TANYIN_UA），密钥类 TANYIN_* 全剥离（真子进程实证）。
2. guard 层拦截执法面写命令：tanyin-ledger approve（approvals.tsv）与
   tanyin-knowledge approvers add（approvers.tsv）对战士降只读。
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli")
GUARD = os.path.join(CLI, "tanyin-guard")
LEDGER = os.path.join(CLI, "tanyin-ledger")
KNOW = os.path.join(CLI, "tanyin-knowledge")
FIX = os.path.join(HERE, "fixtures", "G-g1")
SEED_KN = os.path.join(ROOT, "knowledge")
PY = sys.executable

sys.path.insert(0, CLI)

_loader = SourceFileLoader("tanyin_runner_src", os.path.join(CLI, "tanyin-runner"))
_spec = importlib.util.spec_from_loader("tanyin_runner_src", _loader)
runner = importlib.util.module_from_spec(_spec)
_loader.exec_module(runner)

POISON = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": os.environ.get("HOME", "/tmp"),
    "TANYIN_HOME": "/tmp/tanyin-home",
    "TANYIN_UA": "Neutral/1",
    "TANYIN_APPROVAL_KEY": "operator-secret-key",
    "TANYIN_JUDGE_API_KEY": "judge-secret",
    "TANYIN_JUDGE_BASE_URL": "https://judge.internal",
    "TANYIN_VAULT_SECRET": "vault-secret",
    "TANYIN_VAULT_PASSPHRASE": "vault-pp",
    "TANYIN_VAULT_KEYFILE": "/tmp/vault.key",
    "TANYIN_ZHULONG_PASS": "zl-pass",
    "TANYIN_ZHULONG_USER": "zl-user",
    "TANYIN_ANCHOR_REMOTE": "git@remote:anchor",
    "TANYIN_LLMPOOL_STATE": "x",
    "OPENCODE_CONFIG_DIR": "/tmp/oc",
}
SECRET_VARS = ("TANYIN_APPROVAL_KEY", "TANYIN_JUDGE_API_KEY",
               "TANYIN_JUDGE_BASE_URL", "TANYIN_VAULT_SECRET",
               "TANYIN_VAULT_PASSPHRASE", "TANYIN_VAULT_KEYFILE",
               "TANYIN_ZHULONG_PASS", "TANYIN_ZHULONG_USER",
               "TANYIN_ANCHOR_REMOTE", "TANYIN_LLMPOOL_STATE")


def _guard_exec(gd, ts, *cmd):
    return subprocess.run(
        [PY, GUARD, "exec", "--goal-dir", gd, "--timestamp=" + ts, "--"] + list(cmd),
        capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestWarriorEnvWhitelist(unittest.TestCase):
    def test_strips_secret_class_keeps_basics(self):
        env = runner.warrior_env(POISON)
        for k in SECRET_VARS:
            self.assertNotIn(k, env, "密钥类 env 须剥离: " + k)
        for k in ("PATH", "HOME", "TANYIN_HOME", "TANYIN_UA"):
            self.assertIn(k, env, "必需面须保留: " + k)

    def test_default_base_is_operator_environ(self):
        # 不变量: 缺省 base=操作员 os.environ 经白名单过滤（与调用环境是否带 PATH 无关——
        # 主会话修复: 原断言写死 PATH,在无 PATH 的 harness 里假红;invariant 版两处皆绿）
        expect = {k: v for k, v in os.environ.items() if k in runner.WARRIOR_ENV_ALLOW}
        self.assertEqual(runner.warrior_env(), expect)
        if "PATH" in os.environ:
            self.assertIn("PATH", runner.warrior_env())

    def test_real_child_process_env_scrubbed(self):
        """真子进程实证：kernel 级 env 里密钥不存在（非纸面断言）。"""
        r = subprocess.run(
            [PY, "-c", "import os,json;print(json.dumps(dict(os.environ)))"],
            capture_output=True, text=True, encoding="utf-8",
            env=runner.warrior_env(POISON))
        self.assertEqual(r.returncode, 0, r.stderr)
        child = json.loads(r.stdout)
        for k in SECRET_VARS:
            self.assertNotIn(k, child, "真子进程 env 仍含: " + k)
        self.assertIn("PATH", child)

    def test_launch_passes_whitelisted_env(self):
        """launch() 不再 dict(os.environ)——Popen 收到的 env 即白名单面。"""
        captured = {}

        class _FakeProc:
            pid = 4242

        def _fake_popen(cmd, **kw):
            captured.update(kw.get("env") or {})
            return _FakeProc()

        log_path = os.path.join(tempfile.mkdtemp(prefix="sec1-launch-"), "log")
        old_popen, old_environ = subprocess.Popen, dict(os.environ)
        warnings.simplefilter("ignore", ResourceWarning)  # launch 持有日志句柄=既有设计
        try:
            subprocess.Popen = _fake_popen
            os.environ.clear()
            os.environ.update(POISON)
            proc = runner.launch("/tmp", "prompt", log_path)
        finally:
            subprocess.Popen = old_popen
            os.environ.clear()
            os.environ.update(old_environ)
        self.assertEqual(proc.pid, 4242)
        self.assertNotIn("TANYIN_APPROVAL_KEY", captured)
        self.assertNotIn("TANYIN_JUDGE_API_KEY", captured)
        self.assertIn("PATH", captured)


class TestGuardEnforcementReadonly(unittest.TestCase):
    """approvals/approvers 两账对战士降只读：guard 执写命令=REJECT 落账。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def _timeline(self):
        with open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8") as f:
            return f.read()

    def test_ledger_approve_via_guard_rejected(self):
        r = _guard_exec(self.gd, "2026-09-30T12:00:00Z",
                        PY, LEDGER, "approve", "--goal-dir", self.gd,
                        "--command-hash=" + "a" * 64, "--decision=approved",
                        "--approver=self", "--timestamp=2026-09-30T12:00:00Z")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("只读", r.stdout)
        self.assertIn("guard-reject enforcement-readonly", self._timeline())

    def test_knowledge_approvers_add_via_guard_rejected(self):
        r = _guard_exec(self.gd, "2026-09-30T12:00:00Z",
                        PY, KNOW, "approvers", "add",
                        "--knowledge-dir=" + self.gd,
                        "--approver=self", "--timestamp=2026-09-30T12:00:00Z")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("approvers", r.stdout)
        self.assertIn("guard-reject enforcement-readonly", self._timeline())

    def test_readonly_commands_still_pass(self):
        r = _guard_exec(self.gd, "2026-09-30T12:00:00Z",
                        PY, KNOW, "approvers", "list",
                        "--knowledge-dir=" + SEED_KN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("#count=", r.stdout)

    def test_shell_wrapped_write_also_rejected(self):
        r = _guard_exec(self.gd, "2026-09-30T12:00:00Z",
                        "sh", "-c", LEDGER + " approve --goal-dir " + self.gd
                        + " --command-hash=" + "a" * 64 + " --decision=approved"
                        + " --approver=self --timestamp=2026-09-30T12:00:00Z")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("只读", r.stdout)


if __name__ == "__main__":
    unittest.main()
