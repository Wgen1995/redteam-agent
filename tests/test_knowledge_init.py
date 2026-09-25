# -*- coding: utf-8 -*-
"""批次5 T9：tanyin-knowledge 第 12 员骨架钉子——init 幂等/format_version 门/
种子库在场/种子库只读纪律（R7）/client-map.tsv gitignore 排除（R12）。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KN = os.path.join(HERE, "..", "cli", "tanyin-knowledge")
SEED = os.path.join(HERE, "..", "knowledge")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestKnowledgeInit(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)

    def test_init_creates_skeleton_idempotent(self):
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)
        for sub in ("concepts", "precedents", "entities", "targets", "patterns/core",
                    "patterns/learned", "business", "retros", "methodology", "cve",
                    "sources", "staging/pages", "checklists"):
            self.assertTrue(os.path.isdir(os.path.join(self.d, sub)), "缺目录 " + sub)
        for f in ("format_version", "index.md", "log.md", "overview.md"):
            self.assertTrue(os.path.isfile(os.path.join(self.d, f)))
        self.assertEqual(kn("init", "--knowledge-dir=" + self.d).returncode, 0)  # 幂等

    def test_format_version_gate(self):
        kn("init", "--knowledge-dir=" + self.d)
        with open(os.path.join(self.d, "format_version"), "w", encoding="utf-8") as f:
            f.write("kn-v0")
        r = kn("lint", "--knowledge-dir=" + self.d)   # 任意后续子命令
        self.assertEqual(r.returncode, 2)
        self.assertIn("迁移", r.stderr)

    def test_seed_repo_knowledge_present(self):
        self.assertTrue(os.path.isfile(os.path.join(SEED, "format_version")))
        self.assertTrue(os.path.isfile(os.path.join(SEED, "checklists", "review-checklist.md")))

    def test_readonly_guard_on_seed(self):
        # 种子库（仓库根 knowledge/）只读纪律（R7）：写子命令 REJECT
        r = kn("source-register", "--knowledge-dir=" + SEED,
               "--path=/etc/hosts", "--origin=internal", "--license=MIT")
        self.assertEqual(r.returncode, 1)
        self.assertIn("种子库只读", r.stderr)

    def test_gitignore_excludes_client_map(self):
        with open(os.path.join(HERE, "..", ".gitignore"), encoding="utf-8") as f:
            gi = f.read()
        self.assertIn("knowledge/client-map.tsv", gi)

    def test_usage_lists_13_subcommands(self):
        # Produces 接口：用法输出 13 子命令枚举（契约 09 §3 工具 12 行）
        r = kn()
        self.assertEqual(r.returncode, 2)
        for sub in ("init", "source-register", "lint", "approve", "commit", "export",
                    "match", "neighbors", "nday-match", "score", "promote", "demote",
                    "client-map"):
            self.assertIn(sub, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
