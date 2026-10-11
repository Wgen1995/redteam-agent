# -*- coding: utf-8 -*-
"""v0.7 runtime 抽取试点：bootstrap 单源（幂等/path/utf8）。"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import runtime  # noqa: E402


class TestBootstrap(unittest.TestCase):
    def test_returns_cli_dir_and_inserts_path(self):
        fake = os.path.join(THIS_CLI := os.path.join(HERE, "..", "cli"), "tanyin-x")
        d = runtime.bootstrap(fake)
        self.assertEqual(os.path.realpath(d), os.path.realpath(THIS_CLI))
        self.assertIn(THIS_CLI, sys.path)

    def test_idempotent(self):
        fake = os.path.join(os.path.join(HERE, "..", "cli"), "tanyin-x")
        runtime.bootstrap(fake)
        n = sys.path.count(os.path.join(HERE, "..", "cli"))
        runtime.bootstrap(fake)
        self.assertEqual(n, sys.path.count(os.path.join(HERE, "..", "cli")))

    def test_pilots_migrated(self):
        """试点两脚本（gateloop/redact）已用 runtime.bootstrap：utf8 走单源，
        不再直 import ensure_utf8_stdio/不再手写调用。"""
        for name in ("tanyin-gateloop", "tanyin-redact"):
            src = open(os.path.join(HERE, "..", "cli", name), encoding="utf-8").read()
            self.assertIn("bootstrap(__file__)", src, name + " 未迁移")
            self.assertIn("from ledger.runtime import bootstrap", src, name + " 缺 import")
            self.assertNotIn("from ledger.core import ensure_utf8_stdio", src,
                             name + " 仍直取 utf8 脚手架")
            self.assertNotIn("ensure_utf8_stdio()", src, name + " 残留手写调用")


if __name__ == "__main__":
    unittest.main()
