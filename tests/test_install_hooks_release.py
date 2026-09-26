# -*- coding: utf-8 -*-
"""批次 6 评审收尾 I-1+I-2：install/hooks 三宿主模板真挂载 + tanyin-install --release 通道（TDD 红→绿）。

断言面：
- I-1（计划 T8；install/hooks/ ★ 按宿主差异）：hook_mechanism 宿主安装后
  <install_root>/hooks/<host>.md 在位（幂等覆盖）；模板=生命周期事件→tanyin CLI
  调用示例+占位说明+G-38 实测回传时点（最小可用面）；无机制宿主=Tier 1+披露
  （零文件落装）；模板缺=rc 1 fail-closed（「占位披露 rc 0」中间态废除）。
- I-2（裁决 C 接线）：--release 显式旗标=新锚公钥路径传入 verify 面替换 TEST-ONLY
  缺省锚；tools.lock 未在新钥下重签=rc 1（KEY-MANAGEMENT §5 原子变更中间态
  fail-closed）；交互确认令牌 REPLACE——缺确认/错词/EOF=exit 2 且锚文件字节零变化；
  确认后原子替换锚文件+install-log.tsv release-anchor 行在册。
"""
import io
import os
import shutil
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
REAL_LOCK = os.path.join(REPO, "tools.lock")
REPO_PUB = os.path.join(REPO, "engines", "nuclei", "release.pub")
RESIGN = os.path.join(REPO, "install", "resign-tools-lock.py")
ENV = {**os.environ, "PYTHONUTF8": "1"}


def _can_symlink():
    try:
        with tempfile.TemporaryDirectory() as d:
            os.symlink(os.path.join(d, "t"), os.path.join(d, "l"))
            return True
    except (OSError, NotImplementedError):
        return False


HAVE_SYMLINK = _can_symlink()


def _sha256(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _mint_keypair(d):
    """openssl 临时 P-256 键对（KEY-MANAGEMENT §1 同参）；返回 (priv, pub) 路径。"""
    priv = os.path.join(d, "release-priv.pem")
    pub = os.path.join(d, "release.pub")
    subprocess.run(["openssl", "genpkey", "-algorithm", "EC",
                    "-pkeyopt", "ec_paramgen_curve:P-256", "-out", priv],
                   capture_output=True, check=True, timeout=120)
    subprocess.run(["openssl", "pkey", "-in", priv, "-pubout", "-out", pub],
                   capture_output=True, check=True, timeout=120)
    return priv, pub


def _mint_repo(d, resign_key=None):
    """临时仓根：tools.lock 副本（resign_key 给定=以该私钥整锁重签，§5 原子变更
    前置态）+TEST-ONLY 锚在位（模拟生产钥就绪、仓锚未换的仪式起点）。"""
    repo = os.path.join(d, "repo")
    os.makedirs(os.path.join(repo, "engines", "nuclei"))
    shutil.copyfile(REAL_LOCK, os.path.join(repo, "tools.lock"))
    shutil.copyfile(REPO_PUB, os.path.join(repo, "engines", "nuclei", "release.pub"))
    if resign_key:
        r = subprocess.run([sys.executable, RESIGN,
                            "--lock", os.path.join(repo, "tools.lock"),
                            "--key", resign_key],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=ENV, timeout=600)
        assert r.returncode == 0, r.stdout + r.stderr
    return repo


def _cli(args, stdin=None, timeout=600):
    return subprocess.run([sys.executable, INSTALL_CLI] + args,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=ENV, timeout=timeout,
                          input=stdin, cwd=REPO)


def _opts(d, host="dsh", **kw):
    o = {"install_root": os.path.join(d, "install"), "home": os.path.join(d, "home"),
         "host": host, "repo_root": REPO, "timestamp": TS}
    o.update(kw)
    return o


def _mint_keypair_helper(tc):
    if shutil.which("openssl") is None:
        raise EnvironmentError("openssl 缺")
    td = tempfile.mkdtemp()
    tc.addCleanup(shutil.rmtree, td, True)
    return _mint_keypair(td)


class TestHooksMount(unittest.TestCase):
    """I-1：install/hooks/ 三宿主模板交付+step4 真挂载（幂等）。"""

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_dsh_install_mounts_host_template(self):
        with tempfile.TemporaryDirectory() as d:
            o = _opts(d, host="dsh")
            code, msg = install_core.install(o)
            self.assertEqual(code, 0, msg)
            mounted = os.path.join(o["install_root"], "hooks", "dsh.md")
            self.assertTrue(os.path.isfile(mounted), "hook 模板应真挂载: " + mounted)
            with open(mounted, encoding="utf-8") as f:
                text = f.read()
            for token in ("生命周期事件", "tanyin-", "占位说明", "G-38"):
                self.assertIn(token, text, "最小可用面缺段: " + token)
            with open(os.path.join(o["home"], "install-log.tsv"),
                      encoding="utf-8") as f:
                log = f.read()
            self.assertIn("hooks\trc=0", log)
            self.assertNotIn("占位披露", log, "占位文案应随 I-1 废除（M-5）")
            # 幂等：二次安装模板字节零变化（copy2 覆盖确定形）
            with open(mounted, "rb") as f:
                first = f.read()
            code2, msg2 = install_core.install(o)
            self.assertEqual(code2, 0, msg2)
            with open(mounted, "rb") as f:
                self.assertEqual(first, f.read())

    @unittest.skipUnless(HAVE_SYMLINK, "symlink 权限（Windows 无开发者模式）")
    def test_no_mechanism_host_tier1_disclosure_no_mount(self):
        with tempfile.TemporaryDirectory() as d:
            o = _opts(d, host="walcode")
            code, msg = install_core.install(o)
            self.assertEqual(code, 0, msg)
            self.assertFalse(os.path.exists(
                os.path.join(o["install_root"], "hooks", "walcode.md")),
                "无 hook 机制宿主不得落装模板")
            with open(os.path.join(o["home"], "install-log.tsv"),
                      encoding="utf-8") as f:
                self.assertIn("Tier 1+披露", f.read())

    def test_missing_template_gate_fail(self):
        """hook_mechanism 宿主而模板缺 → rc 1 fail-closed（占位披露态废除）。"""
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "fake-repo")
            os.makedirs(os.path.join(fake, "install", "hosts"))
            os.makedirs(os.path.join(fake, "install", "hooks"))
            with open(os.path.join(fake, "install", "hosts", "codex.json"),
                      "w", encoding="utf-8") as f:
                f.write('{"host": "codex", "hook_mechanism": true}')
            o = _opts(d, host="codex", repo_root=fake)
            code, msg = install_core._step4_hooks(o)
            self.assertEqual(code, 1, msg)
            self.assertIn("模板缺", msg)

    def test_templates_in_repo_minimum_viable(self):
        """三宿主模板在库+最小可用四段（生命周期事件/CLI 调用/占位说明/G-38 时点）。"""
        for host in ("dsh", "opencode", "codex"):
            p = os.path.join(REPO, "install", "hooks", host + ".md")
            self.assertTrue(os.path.isfile(p), p)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            for token in ("生命周期事件", "tanyin-", "占位说明", "G-38"):
                self.assertIn(token, text, "%s 缺段: %s" % (p, token))


class TestReleaseChannel(unittest.TestCase):
    """I-2：tanyin-install --release 信任锚替换通道（裁决 C 接线）。"""

    def test_release_replace_ok(self):
        """新钥已重签整锁+REPLACE 确认 → rc 0 锚原子替换+release-anchor 日志行。"""
        try:
            priv, pub = _mint_keypair_helper(self)
        except EnvironmentError:
            self.skipTest("openssl 缺（ENV）")
            return
        with tempfile.TemporaryDirectory() as d:
            repo = _mint_repo(d, resign_key=priv)
            home = os.path.join(d, "home")
            old_sha = _sha256(os.path.join(repo, "engines", "nuclei", "release.pub"))
            r = _cli(["--release", "--pubkey", pub, "--repo-root", repo,
                      "--home", home, "--timestamp", TS], stdin="REPLACE\n")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            anchor = os.path.join(repo, "engines", "nuclei", "release.pub")
            self.assertEqual(_sha256(anchor), _sha256(pub), "锚文件应被替换为新钥")
            self.assertNotEqual(_sha256(anchor), old_sha)
            with open(os.path.join(home, "install-log.tsv"),
                      encoding="utf-8") as f:
                log = f.read()
            self.assertIn("release-anchor\trc=0", log)

    def test_release_verify_fail_old_lock_gate_fail(self):
        """整锁未在新钥下重签（新钥旧锁中间态）→ rc 1 fail-closed 锚零变化。"""
        try:
            priv, pub = _mint_keypair_helper(self)
        except EnvironmentError:
            self.skipTest("openssl 缺（ENV）")
            return
        with tempfile.TemporaryDirectory() as d:
            repo = _mint_repo(d)                       # 不重签=TEST-ONLY 旧锁
            home = os.path.join(d, "home")
            anchor = os.path.join(repo, "engines", "nuclei", "release.pub")
            with open(anchor, "rb") as f:
                before = f.read()
            r = _cli(["--release", "--pubkey", pub, "--repo-root", repo,
                      "--home", home, "--timestamp", TS], stdin="REPLACE\n")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            with open(anchor, "rb") as f:
                self.assertEqual(before, f.read(), "verify 不过=锚文件字节零变化")

    def test_release_missing_confirm_exit_2(self):
        """缺确认（EOF/错词）→ exit 2 且锚文件零变化（裁决 C：交互确认不静默）。"""
        try:
            priv, pub = _mint_keypair_helper(self)
        except EnvironmentError:
            self.skipTest("openssl 缺（ENV）")
            return
        for stdin_text in ("", "yes\n"):
            with tempfile.TemporaryDirectory() as d:
                repo = _mint_repo(d, resign_key=priv)
                home = os.path.join(d, "home")
                anchor = os.path.join(repo, "engines", "nuclei", "release.pub")
                with open(anchor, "rb") as f:
                    before = f.read()
                r = _cli(["--release", "--pubkey", pub, "--repo-root", repo,
                          "--home", home, "--timestamp", TS], stdin=stdin_text)
                self.assertEqual(r.returncode, 2, (stdin_text, r.stdout))
                with open(anchor, "rb") as f:
                    self.assertEqual(before, f.read())
                with open(os.path.join(home, "install-log.tsv"),
                          encoding="utf-8") as f:
                    self.assertIn("release-anchor\trc=2", f.read())

    def test_release_missing_pubkey_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            r = _cli(["--release", "--repo-root", os.path.join(d, "r"),
                      "--home", os.path.join(d, "h"), "--timestamp", TS])
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_release_requires_timestamp_exit_2(self):
        # --timestamp 必填（禁墙钟进 install-log；与六步安装同纪律）
        try:
            _priv, pub = _mint_keypair_helper(self)
        except EnvironmentError:
            self.skipTest("openssl 缺（ENV）")
            return
        with tempfile.TemporaryDirectory() as d:
            r = _cli(["--release", "--pubkey", pub,
                      "--repo-root", os.path.join(d, "r"),
                      "--home", os.path.join(d, "h")])
            self.assertEqual(r.returncode, 2)

    def test_release_unit_confirm_stream(self):
        """单源单元面：confirm_stream 注入（CLI 外可测）；替换后 verify 面新钥过门。"""
        try:
            priv, pub = _mint_keypair_helper(self)
        except EnvironmentError:
            self.skipTest("openssl 缺（ENV）")
            return
        with tempfile.TemporaryDirectory() as d:
            repo = _mint_repo(d, resign_key=priv)
            o = {"repo_root": repo, "home": os.path.join(d, "home"),
                 "pubkey": pub, "timestamp": TS}
            rc, msg = install_core.release_anchor(
                o, confirm_stream=io.StringIO("REPLACE\n"))
            self.assertEqual(rc, 0, msg)
            self.assertEqual(_sha256(os.path.join(repo, "engines", "nuclei",
                                                  "release.pub")), _sha256(pub))
            # 换锚后 verify 面以新钥复验整锁=PASS（信任锚替换闭环）
            from ledger import supply_chain
            for e in supply_chain.load_lock(os.path.join(repo, "tools.lock")).values():
                ok, why = supply_chain.verify_entry(e, pub)
                self.assertTrue(ok, "%s: %s" % (e["key"], why))


if __name__ == "__main__":
    unittest.main()
