# -*- coding: utf-8 -*-
"""tanyin-guard（批次 2 T1/T2）测试。"""
import os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "..", "cli", "tanyin-guard")
LEDGER = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
PY = sys.executable

def g(gd, *args):
    return subprocess.run([PY, GUARD, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

def ledger(gd, *args):
    return subprocess.run([PY, LEDGER, args[0], "--goal-dir", gd] + list(args[1:]),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

# 跨平台命令载体：py -c pass（/bin/echo、/bin/sh 仅 POSIX，Windows 上 FileNotFoundError）
NOOP = [PY, "-c", "pass"]
ECHO_SECRET = [PY, "-c", "import os,sys; sys.stdout.write('s=' + os.environ.get('TY_CRED_SECRET', ''))"]

class GuardExec(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def test_in_scope_passes_with_ticket(self):
        before = len(open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").readlines())
        r = g(self.gd, "exec", "--", *(NOOP + ["ping api.shop.example"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").readlines()
        self.assertEqual(len(after), before + 1)
        self.assertIn("request-ticket", after[-1])
    def test_out_of_scope_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["touch evil.example"]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("界外目标", r.stdout)
    def test_deny_list_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["shutdown"]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("deny-list", r.stdout)

class GuardScopeExclude(unittest.TestCase):
    """洞 1（批次 2 审计 Critical #1）：exclude 语义缺失——落账 exclude 后 Tier1 必须拒。

    红测试：add-scope --kind=exclude --matcher=banned.shop.example 落账后
    guard exec 带该主机必须 REJECT（当前实测 exit 0 放行）。
    """
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def add_scope(self, kind, matcher):
        r = ledger(self.gd, "add-scope", "--kind=" + kind, "--matcher=" + matcher,
                   "--timestamp=2026-09-23T09:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def timeline(self):
        p = os.path.join(self.gd, "timeline.tsv")
        return open(p, encoding="utf-8").read()
    def test_exclude_rejects_banned_host(self):
        self.add_scope("exclude", "banned.shop.example")
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "banned.shop.example"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("exclude", r.stdout.lower())
    def test_exclude_priority_over_include(self):
        """判定顺序：先 include 命中，再 exclude 命中即拒——exclude 优先于 include。"""
        self.add_scope("exclude", "*.prod.shop.example")
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "v2.prod.shop.example"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("exclude", r.stdout.lower())
        r2 = g(self.gd, "exec", "--", *(NOOP + ["ping", "api.shop.example"]))
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
    def test_oob_host_rejected_as_record_not_tested(self):
        """契约 05：oob=界外回连白名单端点（记不测）——Tier1 对 oob 主机不做主动测试。"""
        self.add_scope("oob", "cb.example")
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "cb.example"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("OOB", r.stdout)
        self.assertIn("reason=oob", self.timeline())


class GuardVault(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        os.makedirs(os.path.join(self.gd, "vault"), exist_ok=True)
        with open(os.path.join(self.gd, "vault", ".key"), "w", encoding="utf-8", newline="\n") as f:
            f.write("k1")
    def tearDown(self):
        self.td.cleanup()
    def test_deploy_inject_tokenize(self):
        r = g(self.gd, "deploy-vault", "--cred=7", "--username=admin", "--secret=TopSecret-9")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(self.gd, "vault", "cred-7.enc"), encoding="utf-8") as f:
            enc = f.read()
        self.assertNotIn("TopSecret", enc)
        r2 = g(self.gd, "inject", "--cred=7", "--timestamp=2026-09-23T08:00:00Z", "--", *(ECHO_SECRET))
        self.assertEqual(r2.returncode, 0)
        self.assertIn("s={{vault:cred-7}}", r2.stdout)
        self.assertNotIn("TopSecret", r2.stdout)
    def test_missing_entry_rejected(self):
        r = g(self.gd, "inject", "--cred=99", "--", *(NOOP + ["x"]))
        self.assertEqual(r.returncode, 1)

class GuardInjectEnforcement(unittest.TestCase):
    """洞 2（批次 2 审计 Critical #2）：inject 通道零执法——

    红测试：deploy-vault 后 guard inject 带界外主机/deny-list 命中必须 REJECT；
    取票流程与 exec 一致；门链先于 vault 取件（执法结论不因凭据缺失而变）。
    """
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        os.makedirs(os.path.join(self.gd, "vault"), exist_ok=True)
        with open(os.path.join(self.gd, "vault", ".key"), "w", encoding="utf-8", newline="\n") as f:
            f.write("k1")
        r = g(self.gd, "deploy-vault", "--cred=7", "--username=admin", "--secret=TopSecret-9")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def tearDown(self):
        self.td.cleanup()
    def timeline(self):
        return open(os.path.join(self.gd, "timeline.tsv"), encoding="utf-8").read()
    def test_out_of_scope_rejected(self):
        r = g(self.gd, "inject", "--cred=7", "--", *(NOOP + ["ping", "evil.example"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("REJECT", r.stdout)
        self.assertIn("界外目标", r.stdout)
    def test_deny_list_rejected(self):
        r = g(self.gd, "inject", "--cred=7", "--", *(NOOP + ["shutdown"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("deny-list", r.stdout)
    def test_scope_gate_before_vault_lookup(self):
        """门链先于 vault 取件：越权请求不因凭据缺失而改判。"""
        r = g(self.gd, "inject", "--cred=99", "--", *(NOOP + ["ping", "evil.example"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标", r.stdout)
    def test_ticket_flow_matches_exec(self):
        r = g(self.gd, "inject", "--cred=7", "--timestamp=2026-09-23T08:10:00Z", "--", *NOOP)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tl = self.timeline()
        self.assertIn("request-ticket", tl)   # 取票与 exec 一致（当前缺失=红）
        self.assertIn("vault-inject", tl)
        self.assertLess(tl.index("request-ticket"), tl.index("vault-inject"))
    def test_in_scope_passes(self):
        r = g(self.gd, "inject", "--cred=7", "--", *(NOOP + ["ping", "api.shop.example"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class GuardHostExtraction(unittest.TestCase):
    """主机提取强化（审计 Important #6）：flag 内嵌（--target=evil.com）、key=value 里的
    URL/主机、localhost/127.0.0.1/::1、IPv6 字面量——全部要被提取并判定；
    反向钉：脚本类参数（含点号代码 token）与纯数字版本号不得误判为主机。
    """
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def test_flag_embedded_host_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["--target=evil.com"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: evil.com", r.stdout)
    def test_flag_embedded_url_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["--endpoint=https://evil.com/path"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: evil.com", r.stdout)
    def test_key_value_url_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["proxy=evil.com:8080"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: evil.com", r.stdout)
    def test_localhost_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "localhost"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: localhost", r.stdout)
    def test_loopback_ipv4_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "127.0.0.1"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: 127.0.0.1", r.stdout)
    def test_ipv6_loopback_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "::1"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: ::1", r.stdout)
    def test_ipv6_literal_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["ping", "2001:db8::1"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: 2001:db8::1", r.stdout)
    def test_bracketed_ipv6_url_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["curl", "-g", "http://[2001:db8::1]/x"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: 2001:db8::1", r.stdout)
    def test_flag_embedded_ipv6_rejected(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["--host=2001:db8::1"]))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("界外目标: 2001:db8::1", r.stdout)
    def test_flag_embedded_in_scope_passes(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["--target=api.shop.example"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def test_script_args_not_misparsed_as_hosts(self):
        r = g(self.gd, "exec", "--", *ECHO_SECRET)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def test_version_like_numbers_not_hosts(self):
        r = g(self.gd, "exec", "--", *(NOOP + ["--ver=1.2.3"]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class GuardStderrTokenize(unittest.TestCase):
    """洞 3（批次 2 审计 Critical #3）：stderr 不脱敏——vault 真值回泄。

    红测试：inject/exec 的子进程 stderr 写入真值（sys.stderr.write(secret)）后，
    总控收到的 stderr 必须是 {{vault:cred-N}} token 形式（当前实测 LEAK[S3CR3T_AUDIT]）。
    stdout/stderr 双流断言。
    """
    SECRET = "S3CR3T_AUDIT"
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
        os.makedirs(os.path.join(self.gd, "vault"), exist_ok=True)
        with open(os.path.join(self.gd, "vault", ".key"), "w", encoding="utf-8", newline="\n") as f:
            f.write("k1")
        r = g(self.gd, "deploy-vault", "--cred=1", "--username=admin", "--secret=" + self.SECRET)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
    def tearDown(self):
        self.td.cleanup()
    def test_exec_stderr_tokenized(self):
        script = "import sys; sys.stderr.write('LEAK[' + " + repr(self.SECRET) + " + ']')"
        r = g(self.gd, "exec", "--", PY, "-c", script)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("{{vault:cred-1}}", r.stderr)
        self.assertNotIn(self.SECRET, r.stderr)
        self.assertNotIn(self.SECRET, r.stdout)
    def test_exec_stdout_and_stderr_both_tokenized(self):
        script = ("import sys; s = " + repr(self.SECRET) +
                  "; sys.stdout.write('O[' + s + ']'); sys.stderr.write('E[' + s + ']')")
        r = g(self.gd, "exec", "--", PY, "-c", script)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("O[{{vault:cred-1}}]", r.stdout)
        self.assertIn("E[{{vault:cred-1}}]", r.stderr)
        self.assertNotIn(self.SECRET, r.stdout + r.stderr)
    def test_inject_stderr_tokenized(self):
        script = ("import os, sys; s = os.environ.get('TY_CRED_SECRET', ''); "
                  "sys.stdout.write('O[' + s + ']'); sys.stderr.write('E[' + s + ']')")
        r = g(self.gd, "inject", "--cred=1", "--", PY, "-c", script)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("O[{{vault:cred-1}}]", r.stdout)
        self.assertNotIn(self.SECRET, r.stdout)
        self.assertIn("E[{{vault:cred-1}}]", r.stderr)
        self.assertNotIn(self.SECRET, r.stderr)


class GuardDenyListVariants(unittest.TestCase):
    """deny-list 数据化（审计 Important #5）：shared/DENYLIST.md 全形态——
    rm -rf/rm -fr 相对路径变体/drop database/truncate table/fork bomb 等，变体钉死。
    """
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.gd = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))
    def tearDown(self):
        self.td.cleanup()
    def assert_reject(self, *payload):
        r = g(self.gd, "exec", "--", *(NOOP + list(payload)))
        self.assertEqual(r.returncode, 1, "应拒: %r -> %r %r" % (payload, r.stdout, r.stderr))
        self.assertIn("deny-list", r.stdout)
    def test_rm_relative_variants(self):
        self.assert_reject("rm", "-fr", "./x")
        self.assert_reject("rm", "-rf", "./tmp")
        self.assert_reject("rm", "-fr", ".")
        self.assert_reject("rm", "-rf", "/")
    def test_sql_destructive(self):
        self.assert_reject("psql", "-c", "drop database prod;")
        self.assert_reject("psql", "-c", "truncate table users;")
    def test_fork_bomb(self):
        self.assert_reject(":(){:|:&};:")
        self.assert_reject("sh", "-c", ":(){ :|:& };:")
    def test_disk_and_power(self):
        self.assert_reject("dd", "if=/dev/zero", "of=/dev/sda")
        self.assert_reject("mkfs.ext4", "/dev/sdb")
        self.assert_reject("format c:")
        self.assert_reject("shutdown", "-h", "now")
        self.assert_reject("reboot")
        self.assert_reject("init", "0")
        self.assert_reject("chmod", "-R", "777", "/")
    def test_redirect_to_device(self):
        self.assert_reject("bash", "-c", "cat x > /dev/sda")
    def test_benign_passes(self):
        # 注：点分裸参数（如 report.txt）属参数级主机扫描的既有 fail-closed 语义，
        # 非 deny-list 误伤——良性对照用非点分负载。
        for payload in (["echo", "hello world"], ["cat", "notes"], ["ls", "-la"]):
            r = g(self.gd, "exec", "--", *(NOOP + payload))
            self.assertEqual(r.returncode, 0, "误伤: %r -> %r %r" % (payload, r.stdout, r.stderr))


if __name__ == "__main__":
    unittest.main()
