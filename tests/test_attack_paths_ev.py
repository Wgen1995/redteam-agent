# -*- coding: utf-8 -*-
"""批次5 T8：攻击路径进 EV——P4「攻击链落证」步（G-28 后半）。

双钉：①P4.md duty 步文本在场；②diff-authz 夹具副本上集成走查——graph-paths 输出
落盘 artifact → add-evidence 落账 → validate/verify-chain/hash-recheck 全过。
Ruling（接口实况，契约随行）：计划测试片段按 add-evidence 旧接口书写
（--artifact-path/--content-hash-raw/--content-hash-norm/--card-path）——批次 4 评审
C-1 单源化后实况=--artifact 传路径、双指纹由命令自算（cli/ledger/norm.py
artifact_hashes 单源，LLM 不经手哈希）、card_path 自动派生 evidence/<id>.md；
计划意图「总控算哈希=命令算，LLM 不手算」由命令内自算更强兑现。另：P4 duty 实况
4 步（计划称第 6 步），攻击链落证按追加序落第 5 步。"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CLI = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "diff-authz")
TS = "2026-09-24T10:00:00Z"
REPRO = "cli/tanyin-ledger graph-paths --from=AST-g1-0001 --to=scope-root"


def run_ledger(gd, sub, *args):
    return subprocess.run([sys.executable, CLI, sub, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestAttackPathsEv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = shutil.copytree(FIX, os.path.join(self.tmp, "diff-authz"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _cast_artifact(self, name):
        """总控侧机械步：graph-paths stdout 原样存盘（只增不覆盖——重跑换 -r2 后缀）。"""
        r = run_ledger(self.d, "graph-paths", "--from=AST-g1-0001", "--to=scope-root")
        self.assertEqual(r.returncode, 0, r.stderr)
        art = os.path.join(self.d, "evidence", name)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(r.stdout)
        return r.stdout

    def _add_evidence(self, artifact):
        return run_ledger(self.d, "add-evidence", "--title=攻击链落证",
                          "--source-type=capture", "--observed-at=" + TS,
                          "--network-position=intranet",
                          "--repro-command=" + REPRO, "--repro-kind=single",
                          "--artifact=" + artifact,
                          "--raw-excerpt=AST-g1-0001", "--timestamp=" + TS)

    def test_p4_duty_has_step(self):
        t = open(os.path.join(ROOT, "phases", "P4.md"), encoding="utf-8").read()
        self.assertIn("攻击链落证", t)
        self.assertIn("graph-paths", t)
        self.assertIn("attack-paths.txt", t)
        self.assertIn("只增不覆盖", t, "重跑 -r2 后缀纪律须在 duty 文内")

    def test_end_to_end_walk_on_fixture(self):
        out = self._cast_artifact("attack-paths.txt")
        r2 = self._add_evidence("evidence/attack-paths.txt")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        ev_id = r2.stdout.splitlines()[0].split(chr(9))[1]
        self.assertTrue(ev_id.startswith("EV-"))
        # EV 双指纹=命令自算（norm.py 单源）——hash-recheck 复算一致
        self.assertEqual(run_ledger(self.d, "validate").returncode, 0)
        self.assertEqual(run_ledger(self.d, "verify-chain").returncode, 0)
        self.assertEqual(run_ledger(self.d, "hash-recheck").returncode, 0)
        # artifact 只增不覆盖：同路径重跑=REJECT；-r2 后缀=放行
        r3 = self._add_evidence("evidence/attack-paths.txt")
        self.assertEqual(r3.returncode, 1)
        self.assertIn("只增不覆盖", r3.stderr + r3.stdout)
        self._cast_artifact("attack-paths-r2.txt")
        r4 = self._add_evidence("evidence/attack-paths-r2.txt")
        self.assertEqual(r4.returncode, 0, r4.stdout + r4.stderr)
        self.assertEqual(run_ledger(self.d, "hash-recheck").returncode, 0)
        self.assertIn("AST-g1-0001", out, "artifact 首条路径行在场")


if __name__ == "__main__":
    unittest.main()
