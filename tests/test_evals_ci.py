# tests/test_evals_ci.py
# -*- coding: utf-8 -*-
"""T4 CI 全量化：evals job 接线契约在场断言（文本级；批次 6）。"""
import os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))


class TestCiWiring(unittest.TestCase):
    def setUp(self):
        p = os.path.join(HERE, "..", ".github", "workflows", "ci.yml")
        with open(p, "r", encoding="utf-8") as f:
            self.yml = f.read()

    def test_static_step_present(self):
        self.assertIn("tanyin-evals run --suite=static", self.yml)

    def test_dynamic_job_present(self):
        self.assertIn("evals-dynamic", self.yml)
        self.assertIn("--suite=dynamic", self.yml)

    def test_artifact_upload(self):
        self.assertIn("actions/upload-artifact", self.yml)

    def test_env_flag(self):
        self.assertIn("PYTHONUTF8", self.yml)  # 既有纪律延续


if __name__ == "__main__":
    unittest.main()
