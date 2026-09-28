# -*- coding: utf-8 -*-
"""批次 8 T6（M15）：安装卸载面——只增不删混版（SRE 反例）收口。
uninstall：删权威安装树；home（交战区=真实数据）默认保留须 --purge-home；
幂等（二次 rc=0 already-clean）；install-log 落 uninstall 行。
"""
import os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import install_core

REPO = os.path.join(HERE, "..")
CLI = os.path.join(REPO, "cli", "tanyin-install")
TS = "2026-09-27T12:00:00Z"


def opts(d, **kw):
    o = {"install_root": os.path.join(d, "install"), "home": os.path.join(d, "home"),
         "host": "dsh", "repo_root": REPO, "timestamp": TS}
    o.update(kw)
    return o


class TestUninstall(unittest.TestCase):
    def test_uninstall_idempotent_home_kept(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            code, msg = install_core.install(o)
            self.assertEqual(code, 0, msg)
            self.assertTrue(os.path.isdir(os.path.join(o["install_root"], "cli")))
            eng = os.path.join(o["home"], "engagements")
            os.makedirs(eng, exist_ok=True)
            rc, msg = install_core.uninstall(o)
            self.assertEqual(rc, 0, msg)
            self.assertFalse(os.path.exists(o["install_root"]), "安装树必须整体移除")
            self.assertTrue(os.path.isdir(eng), "home 交战区默认保留（真实数据不随卸载销毁）")
            log = open(os.path.join(o["home"], "install-log.tsv"), encoding="utf-8").read()
            self.assertIn("uninstall", log)
            rc2, msg2 = install_core.uninstall(o)
            self.assertEqual(rc2, 0, "幂等：二次卸载 already-clean rc=0： %s" % msg2)

    def test_cli_uninstall_face(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            install_core.install(o)
            r = subprocess.run([sys.executable, CLI, "uninstall",
                                "--install-root", o["install_root"],
                                "--home", o["home"], "--timestamp", TS],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(o["install_root"]))

    def test_purge_home_opt_in(self):
        with tempfile.TemporaryDirectory() as d:
            o = opts(d)
            install_core.install(o)
            rc, _ = install_core.uninstall(o, purge_home=True)
            self.assertEqual(rc, 0)
            self.assertFalse(os.path.exists(o["home"]), "--purge-home 显式销毁交战区 home")


if __name__ == "__main__":
    unittest.main()
