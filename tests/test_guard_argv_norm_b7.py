# -*- coding: utf-8 -*-
"""批次 7 T4/T5：guard exec argv 规范化 + 主机提取硬化（C2 反例全录）。

T4 红=专家实测 `rm -r -f /` rc=0：deny-list 子串比对只认字面「rm -rf /」，
组合短旗标/长旗标/换序/大小写混写/内嵌 payload 全部逃逸。
T5 红=专家实测 `http://134744072/`（十进制 8.8.8.8）rc=0：主机提取不认
变体编码，界外判定被整段绕过；控制组 evil.com 正常 REJECT 不受扰。

红例复现安全纪律（R-T4-2）：guard 层测试一律经 _shim_env 注入 PATH 替身
目录（rm/sh/curl/echo 假体 exit 0）——红测证明的是「门放行 rc=0」的执法
逃逸，不由测试真实执行破坏载荷；绿态 REJECT 先于 subprocess.run，行为面
与直跑完全一致。
"""
import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from tests.test_dryrun_p0p2 import fresh_drydir

GUARD = os.path.join(ROOT, "cli", "tanyin-guard")
PY = sys.executable

def _shim_env(names=("rm", "sh", "curl", "echo")):
    """PATH 前置替身目录：载荷假体 exit 0（红态逃逸可见=rc 0，零真实执行）。"""
    d = tempfile.mkdtemp(prefix="guard-shim-")
    for n in names:
        p = os.path.join(d, n)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("#!/bin/sh\nexit 0\n")
        if os.name != "nt":
            os.chmod(p, 0o755)
    env = dict(os.environ)
    env["PATH"] = d + os.pathsep + env.get("PATH", "")
    return env

def run_guard(gd, *cmd):
    return subprocess.run([PY, GUARD, "exec", "--goal-dir", gd, '--timestamp=2026-09-30T12:00:00Z', "--"] + list(cmd),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=_shim_env())

# 专家复现命令全录（台账 C2 反例一 + 工程化变体）
REPROS = [
    ["rm", "-r", "-f", "/"],                 # 专家原例
    ["rm", "-f", "-r", "/"],                 # 换序
    ["rm", "--recursive", "--force", "/"],   # 长旗标
    ["rm", "-rF", "/"],                      # 组合+大小写混写
    ["rm", "-r", "-f", "./"],                # ./ 变体
    ["sh", "-c", "rm -r -f /"],              # 内嵌 payload
]

class TestNormalize(unittest.TestCase):
    def test_normalize_joins_flags(self):
        from ledger.enforce import normalize_cmd
        self.assertEqual(normalize_cmd(["rm", "-r", "-f", "/"]), ["rm", "-fr", "/"])
        self.assertEqual(normalize_cmd(["rm", "--recursive", "--force", "/"]), ["rm", "-fr", "/"])
        self.assertEqual(normalize_cmd(["curl", "-s", "-L", "http://x/"]), ["curl", "-ls", "http://x/"])

    def test_deny_forms_embeds_payload(self):
        from ledger.enforce import deny_forms
        forms = deny_forms(["sh", "-c", "rm -r -f /"])
        self.assertTrue(any("rm -fr /" in f for f in forms), "归一形必须覆盖内嵌 payload")

class TestGuardReject(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def test_expert_repros_all_rejected(self):
        gd = fresh_drydir(self.td.name, "G-norm")
        for cmd in REPROS:
            r = run_guard(gd, *cmd)
            self.assertEqual(r.returncode, 1, "REJECT rc=1: %r\n%s%s" % (cmd, r.stdout, r.stderr))
            self.assertIn("deny-list", r.stdout, "拒绝原因=deny-list 命中: %r" % cmd)

    def test_benign_flags_unaffected(self):
        gd = fresh_drydir(self.td.name, "G-norm2")
        r = run_guard(gd, PY, "-c", "print(1)")
        self.assertNotIn("deny-list", r.stdout, "良性旗标不得误伤")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


# ---- T5：guard 主机提取硬化（C2 反例二）----
# 红=专家实测 http://134744072/（十进制 8.8.8.8）rc=0：主机提取不认变体编码，
# 界外判定被整段绕过；控制组 evil.com 正常 REJECT 不受扰（test_guard 既有面）。

# 专家复现命令全录（台账 C2 反例二 + 工程化变体）
IP_REPROS = [
    (["curl", "http://134744072/"],  "8.8.8.8"),    # 专家原例：十进制
    (["echo", "http://134744072/"],  "8.8.8.8"),    # 专家原例载体：echo（执行面零风险）
    (["curl", "http://2130706433/"], "127.0.0.1"),  # 十进制环回
    (["curl", "http://0x7f000001/"], "127.0.0.1"),  # 十六进制
    (["curl", "http://0177.0.0.1/"], "127.0.0.1"),  # 八进制段
    (["curl", "http://0x08080808/"], "8.8.8.8"),    # 十六进制整段
]

class TestHostDeobfuscation(unittest.TestCase):
    def test_unit_decode(self):
        from ledger.enforce import _decode_ip_obfuscation
        self.assertEqual(_decode_ip_obfuscation("134744072"), "8.8.8.8")
        self.assertEqual(_decode_ip_obfuscation("0x7f000001"), "127.0.0.1")
        self.assertEqual(_decode_ip_obfuscation("0177.0.0.1"), "127.0.0.1")
        self.assertEqual(_decode_ip_obfuscation("example.com"), "example.com", "域名原样")
        self.assertEqual(_decode_ip_obfuscation("3.14"), "3.14", "版本号不解码不误判")
        self.assertEqual(_decode_ip_obfuscation("1.2.3"), "1.2.3", "三段短式不解码")

    def test_extract_hosts_decodes(self):
        from ledger.enforce import extract_hosts
        self.assertEqual(extract_hosts(["curl", "http://134744072/"]), ["8.8.8.8"])
        self.assertEqual(extract_hosts(["curl", "http://0177.0.0.1/x"]), ["127.0.0.1"])

    def test_guard_rejects_decimal_ip_out_of_scope(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = fresh_drydir(td.name, "G-ip")
        for cmd, host in IP_REPROS:
            r = run_guard(gd, *cmd)
            self.assertEqual(r.returncode, 1, "REJECT: %r\n%s" % (cmd, r.stdout))
            self.assertIn(host, r.stdout, "拒绝消息必须出示解码后主机: %r" % cmd)

    def test_guard_version_number_not_flagged(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = fresh_drydir(td.name, "G-ip2")
        r = run_guard(gd, PY, "--version=3.14")
        self.assertNotIn("REJECT", r.stdout, "版本号值段不得被当主机拒")
        self.assertNotIn("3.14", r.stdout.replace("--version=3.14", ""), "版本号值段不得被当主机拒")
