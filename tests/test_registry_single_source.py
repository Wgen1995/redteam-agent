# -*- coding: utf-8 -*-
"""W2 枚举单源化②：命令面注册表单源——zhulong_export 归 registry._MODULES 在册。

红现状：Ship Z 经 tanyin-ledger 入口在组装期 patch registry._MODULES（跨模块改
私有属性，02 评审 P0-2② 点名）——纯 registry 导入（不经入口副作用）时
zhulong-export 不可派发/不入 all_commands，命令面存在第二份组装真相。"""
import os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))


def _fresh_registry_probe():
    """全新解释器探针：只 import ledger.registry（零入口副作用），回归 registry 自身真相。"""
    code = (
        "import sys; sys.path.insert(0, 'cli')\n"
        "from ledger import registry\n"
        "assert 'zhulong_export' in registry._MODULES, 'zhulong_export 不在模块表'\n"
        "assert registry.lookup('zhulong-export') is not None, 'zhulong-export 不可派发'\n"
        "assert 'zhulong-export' in registry.all_commands(), 'zhulong-export 不在命令面'\n"
    )
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestRegistryOwnsZhulong(unittest.TestCase):
    def test_fresh_import_dispatches_zhulong(self):
        r = _fresh_registry_probe()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_entry_does_not_patch_private_module_table(self):
        with open(os.path.join(ROOT, "cli", "tanyin-ledger"), encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("_MODULES", src,
                         "入口不得跨模块改 registry 私有属性（注册面归 registry 单源）")


if __name__ == "__main__":
    unittest.main()


class TestSelfcheckLedgerFaceDerived(unittest.TestCase):
    """W2 枚举单源化④：selfcheck KNOWN_COMMANDS["ledger"]=registry 派生（禁手抄表）。

    红现状：68 名手抄冻结清单（selfcheck.py:33——02 评审 P0-2④ 点名「手抄表改
    registry 派生断言」）；派生面=dispatch_face()（builtin 三条+全 HANDLERS 键
    含 ledger- 前缀孪生）——新命令落 registry 即自动入白名单，忘登记类漂移绝根。"""

    def test_registry_exposes_dispatch_face(self):
        from ledger import registry
        face = registry.dispatch_face()
        self.assertIsInstance(face, frozenset)
        for must in ("validate", "verify-chain", "next-id", "add-goal",
                     "ledger-add-goal", "zhulong-export", "intent-lease"):
            self.assertIn(must, face, "派发面缺 %s" % must)

    def test_selfcheck_ledger_known_equals_dispatch_face(self):
        from ledger import registry, selfcheck
        self.assertEqual(frozenset(selfcheck.KNOWN_COMMANDS["ledger"]),
                         registry.dispatch_face(),
                         "KNOWN_COMMANDS['ledger'] 须=registry 派发面单源派生")

    def test_known_ledger_covers_handcopied_history(self):
        # 防回退钉：派生面 ⊇ 历手抄清单全部成员（含 Ship Z/intent-lease 追登记）
        from ledger import selfcheck
        historical = {"add-goal", "add-finding", "supersede-finding", "anchor",
                      "intent-lease", "zhulong-export", "ledger-matrix-set",
                      "ledger-terminal-gate", "next-id", "validate"}
        self.assertTrue(historical <= frozenset(selfcheck.KNOWN_COMMANDS["ledger"]))
