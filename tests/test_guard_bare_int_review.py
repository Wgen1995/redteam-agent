# -*- coding: utf-8 -*-
"""批次 7 评审收尾 I-2：guard 裸整数误伤回归收口（T5 解码候选集过宽）。

红=评审七形亲测误拒实录（良性对照面）：argv 裸整数被 _decode_ip_obfuscation
无条件解码进主机候选（sleep 3→0.0.0.3、chmod 644→0.0.2.132、head -n 5→0.0.0.5、
sort -k 2→0.0.0.2、nmap -p 443→0.0.1.187、curl -m 30→0.0.0.30、ssh -p 2222→
0.0.8.174），fresh 夹具 scope 缺失=fail-closed 七形一律 REJECT 界外。
修法（评审建议）=解码语境门外置：URL（含 ://）/userinfo（@）/host:port（剥端口
前含冒号）/含点形态之外，裸整数不进候选。

专家反例不许回退：IP 混淆反例九形（URL 语境/含点形态）仍全 REJECT 且消息出示
解码后主机；非 URL 的 @/host:port/含点三语境解码能力由用例钉死不阉割。

红例复现安全纪律（R-T4-2 同律）：guard 层七形一律经 shim 替身目录执行（exit 0
假体）——红态证明的是「门误拒 rc=1」，绿态 rc=0 由假体承载，零真实执行。
"""
import os, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from tests.test_dryrun_p0p2 import fresh_drydir

GUARD = os.path.join(ROOT, "cli", "tanyin-guard")
PY = sys.executable

# 评审七形亲测误拒实录（原文 argv 逐字；解码产物=红态 REJECT 消息在证）
BARE_INT = [
    (["sleep", "3"], "0.0.0.3"),
    (["chmod", "644"], "0.0.2.132"),
    (["head", "-n", "5"], "0.0.0.5"),
    (["sort", "-k", "2"], "0.0.0.2"),
    (["nmap", "-p", "443"], "0.0.1.187"),
    (["curl", "-m", "30"], "0.0.0.30"),
    (["ssh", "-p", "2222"], "0.0.8.174"),
]

# IP 混淆反例九形（专家反例不许回退：前六形=T5 IP_REPROS 原样；后三形=评审收尾补录
# 元数据 IP 三编码变体，全为 URL 语境——解码语境门收窄后仍须全 REJECT）
IP_OBF_NINE = [
    (["curl", "http://134744072/"], "8.8.8.8"),            # 专家原例：十进制
    (["echo", "http://134744072/"], "8.8.8.8"),            # 专家原例载体：echo
    (["curl", "http://2130706433/"], "127.0.0.1"),         # 十进制环回
    (["curl", "http://0x7f000001/"], "127.0.0.1"),         # 十六进制
    (["curl", "http://0177.0.0.1/"], "127.0.0.1"),         # 八进制段
    (["curl", "http://0x08080808/"], "8.8.8.8"),           # 十六进制整段
    (["curl", "http://2852039166/"], "169.254.169.254"),   # 十进制元数据地址
    (["curl", "http://0xA9FEA9FE/"], "169.254.169.254"),   # 十六进制元数据地址
    (["curl", "http://0251.0376.0251.0376/"], "169.254.169.254"),  # 八进制段点分
]


def _shim_env(names=("sleep", "chmod", "head", "sort", "nmap", "curl", "ssh", "echo")):
    """PATH 前置替身目录：载荷假体 exit 0（红态误拒 rc=1 可见，绿态放行 rc=0 零真实执行）。"""
    d = tempfile.mkdtemp(prefix="guard-shim-bare-")
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


class TestBareIntNotHosts(unittest.TestCase):
    """红=七形亲测误拒实录进测试（良性对照面）。"""

    def test_unit_bare_int_not_in_candidates(self):
        from ledger.enforce import extract_hosts, _decode_ip_obfuscation
        # 解码函数本身保持可用（单元面不变，语境门在调用侧）
        self.assertEqual(_decode_ip_obfuscation("134744072"), "8.8.8.8")
        for cmd, _bad in BARE_INT:
            self.assertEqual(extract_hosts(cmd), [],
                             "裸整数不得解码为主机候选: %r" % (cmd,))

    def test_guard_seven_bare_int_forms_pass(self):
        for cmd, _bad in BARE_INT:
            td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
            gd = fresh_drydir(td.name, "G-bare")
            r = run_guard(gd, *cmd)
            self.assertEqual(r.returncode, 0,
                             "良性裸整数误拒（红）: %r\n%s%s" % (cmd, r.stdout, r.stderr))
            self.assertNotIn("REJECT", r.stdout, "良性命令不得 REJECT: %r" % (cmd,))

    def test_host_contexts_still_decoded(self):
        """语境门外置不阉割：@/host:port/含点三语境解码能力钉死（反矫枉过正面）。"""
        from ledger.enforce import extract_hosts
        self.assertEqual(extract_hosts(["ssh", "root@2130706433"]), ["127.0.0.1"],
                         "userinfo(@) 语境仍解码")
        self.assertEqual(extract_hosts(["curl", "2130706433:8080"]), ["127.0.0.1"],
                         "host:port 语境仍解码")
        self.assertEqual(extract_hosts(["nmap", "0177.0.0.1"]), ["127.0.0.1"],
                         "含点形态仍解码")


class TestObfuscationNineNotRegressed(unittest.TestCase):
    """专家反例不许回退：IP 混淆九形仍全 REJECT，消息出示解码后主机。"""

    def test_nine_forms_all_rejected(self):
        for cmd, host in IP_OBF_NINE:
            td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
            gd = fresh_drydir(td.name, "G-obf")
            r = run_guard(gd, *cmd)
            self.assertEqual(r.returncode, 1, "REJECT rc=1: %r\n%s" % (cmd, r.stdout))
            self.assertIn(host, r.stdout, "拒绝消息必须出示解码后主机: %r" % (cmd,))


if __name__ == "__main__":
    unittest.main()
