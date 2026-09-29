# -*- coding: utf-8 -*-
"""批次 8 T10b（M1 尾）：退出码分型——环境域错（文件缺/不可读）须 exit 2 非 1。
样例面：tanyin-replay 卡片文件不可读（E-index 行在、卡片文件缺=环境非门禁）。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPLAY = os.path.join(ROOT, "cli", "tanyin-replay")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-27T12:00:00Z"


class TestEnvExitTyping(unittest.TestCase):
    def test_replay_missing_card_file_env_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            gd = os.path.join(td, "G")
            shutil.copytree(FIX, gd)
            # E-index 行在场、卡片文件抽走=环境域（非门禁判定失败）
            for root, _d, files in os.walk(gd):
                for f in files:
                    if f.startswith("EV-") and f.endswith(".md"):
                        os.remove(os.path.join(root, f))
            r = subprocess.run([sys.executable, REPLAY, "replay", "--goal-dir", gd,
                                "--id=EV-g1-0001", "--timestamp", TS],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            self.assertEqual(r.returncode, 2,
                             "卡片文件缺=环境域 exit 2（红现状 rc=1 门禁域）: %s" % r.stderr)


if __name__ == "__main__":
    unittest.main()
