# -*- coding: utf-8 -*-
"""批次 6 T5：tanyin-install 六步安装器（TDD 红→绿）。

断言面：六步退出码 0/1/2 裁决（1=lock 验签不过 fail-closed；2=openssl/pubkey 缺 ENV）、
权威目录落装、宿主链接、R-T12-4 k1-baseline 拷贝兑现、幂等（二次安装零变更）、
交战区分离（§3.4：home 永不在安装树内）、CLI 面（--list-hosts/--timestamp 必填）。"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import install_core  # noqa: E402

TS = "2026-09-24T00:00:00Z"
INSTALL_CLI = os.path.join(REPO, "cli", "tanyin-install")
ENV = {**os.environ, "PYTHONUTF8": "1"}


def _can_symlink():
    try:
        with tempfile.TemporaryDirectory() as d:
            os.symlink(os.path.join(d, "t"), os.path.join(d, "l"))
            return True
    except (OSError, NotImplementedError):
        return False


HAVE_SYMLINK = _can_symlink()


def opts(d, host="dsh", **kw):
    o = {"install_root": os.path.join(d, "install"), "home": os.path.join(d, "home"),
         "host": host, "repo_root": REPO, "timestamp": TS}
    o.update(kw)
    return o


class TestInstall(unittest.TestCase):
    def test_step1_tampered_lock_gate_fail(self):
        """被篡改 tools.lock + 真钥：verify-lock 必须 rc=1（fail-closed 门禁失败）。"""
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "fake-repo")
            os.makedirs(fake)
            with open(os.path.join(REPO, "tools.lock"), encoding="utf-8") as f:
                lock = f.read()
            tampered = lock.replace(
                "4802fd7bea530e539999bca3ead9903a38fd8ee95a9b6412bb125c271b630754",
                "0802fd7bea530e539999bca3ead9903a38fd8ee95a9b6412bb125c271b630754")
            self.assertNotEqual(lock, tampered, "篡改探针必须命中真 sha256 字节")
            with open(os.path.join(fake, "tools.lock"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write(tampered)
            code, msg = install_core.install(opts(
                d, repo_root=fake,
                pubkey=os.path.join(REPO, "engines", "nuclei", "release.pub")))
            self.assertEqual(code, 1, msg)
            self.assertIn("verify-lock=1", msg)  # 摘要=step=rc 形态；明细在安装日志
            with open(os.path.join(d, "home", "install-log.tsv"), encoding="utf-8") as f:
                log = f.read()
            self.assertIn("验签失败", log)

    def test_step1_missing_pubkey_env(self):
        """钥文件缺=ENV（rc=2）；签名不符才是 1（fail-closed 语义两态分离）。"""
        with tempfile.TemporaryDirectory() as d:
            bad = install_core.install(opts(
                d, pubkey=os.path.join(HERE, "fixtures", "keys",
                                       "test-signing-key.pem") + ".nonexistent"))
            self.assertEqual(bad[0], 2, bad[1])
            self.assertIn("verify-lock=2", bad[1])

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_steps_2_5_skeleton(self):
        with tempfile.TemporaryDirectory() as d:
            code, msg = install_core.install(opts(d))
            self.assertEqual(code, 0, msg)
            o = opts(d)
            ir, hm = o["install_root"], o["home"]
            for p in ("SKILL.md", "phases", "engines", "cli", "shared", "tools.lock"):
                self.assertTrue(os.path.exists(os.path.join(ir, p)), p)      # step2 权威目录
            self.assertTrue(os.path.exists(os.path.join(hm, "engagements")))  # step5 交战区
            self.assertTrue(os.path.exists(
                os.path.join(hm, "knowledge", "methodology", "k1-baseline.tsv")),
                "R-T12-4：安装器拷贝 k1-baseline 兑现")
            self.assertTrue(os.path.exists(os.path.join(hm, "install-log.tsv")))
            # step3 链接断言（计划注：以 link_report 非空+目标存在为准）
            rep = install_core.link_report(o)
            self.assertTrue(rep["links"], "dsh 模板应产出 skill 链接")
            for target, ok in rep["links"]:
                self.assertTrue(ok, target)
                self.assertTrue(os.path.islink(target), target)
                self.assertTrue(os.path.exists(target), "链接目标悬空: " + target)
            # 安装日志：六步各一行、显式时间戳、三列 TSV
            with open(os.path.join(hm, "install-log.tsv"), encoding="utf-8") as f:
                rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
            self.assertEqual([r[1] for r in rows], list(install_core.STEPS))
            for r in rows:
                self.assertEqual(len(r), 3, r)
                self.assertEqual(r[0], TS, "时间戳必须显式字面量")

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_host_link_conflict_rejected(self):
        """目标位置已有真实文件（非链接）→ rc=1 冲突拒装，用户文件零触碰。"""
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            tgt = os.path.join(o["home"], "hosts", "dsh", "skills", "tanyin")
            os.makedirs(os.path.dirname(tgt))
            with open(tgt, "w", encoding="utf-8") as f:
                f.write("user data")
            code, msg = install_core.install(o)
            self.assertEqual(code, 1, msg)
            with open(os.path.join(o["home"], "install-log.tsv"), encoding="utf-8") as f:
                self.assertIn("冲突", f.read())  # 摘要=step=rc 形态；明细在安装日志
            with open(tgt, encoding="utf-8") as f:
                self.assertEqual(f.read(), "user data")

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_idempotent_second_run(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            first, msg1 = install_core.install(o)
            self.assertEqual(first, 0, msg1)
            snap1 = install_core.snapshot(o["install_root"], o["home"])
            second, msg2 = install_core.install(o)
            self.assertEqual(second, 0, msg2)
            snap2 = install_core.snapshot(o["install_root"], o["home"])
            self.assertEqual(snap1, snap2, "二次安装必须零变更（§10.1 幂等）")

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_engagement_zone_separation(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            install_core.install(o)
            ir, hm = os.path.abspath(o["install_root"]), os.path.abspath(o["home"])
            self.assertFalse(hm == ir or hm.startswith(ir + os.sep),
                             "交战区永不在安装树内（§3.4）")

    def test_separation_against_repo(self):
        # 仓内自检形态：默认 install_root/home 均不得落在 repo 树内
        self.assertFalse(install_core.DEFAULT_INSTALL_ROOT_expanded().startswith(REPO))
        self.assertFalse(install_core.DEFAULT_HOME_expanded().startswith(REPO))


class TestInstallCli(unittest.TestCase):
    def test_list_hosts(self):
        r = subprocess.run([sys.executable, INSTALL_CLI, "--list-hosts"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=ENV, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for h in ("dsh", "opencode", "codex", "walcode", "codebuddy"):
            self.assertIn(h, r.stdout)
        self.assertIn("静态验证+待实测", r.stdout)  # §10.3 发布口径

    def test_timestamp_required_exit_2(self):
        # --timestamp 必填；argparse 用法错误退出码 2=退出码契约同形
        r = subprocess.run([sys.executable, INSTALL_CLI, "--install-root", "x",
                            "--home", "y"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV, timeout=120)
        self.assertEqual(r.returncode, 2)

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_cli_install_run_ok(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(
                [sys.executable, INSTALL_CLI,
                 "--install-root", os.path.join(d, "ir"),
                 "--home", os.path.join(d, "hm"),
                 "--timestamp", TS],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", env=ENV, timeout=600, cwd=REPO)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("verify-lock=0", r.stdout)
            self.assertTrue(os.path.exists(os.path.join(d, "hm", "install-log.tsv")))


if __name__ == "__main__":
    unittest.main()
