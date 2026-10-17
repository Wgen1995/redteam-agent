# -*- coding: utf-8 -*-
"""W2 枚举单源化③：docs/gen_counts.py 计数生成器——单源派生+快照同步+活文档口径机检。

三钉：①counts.json 字节快照=生成器输出（--check 门禁：漂移 rc=1/环境 rc=2）；
②计数自单源派生（命令面=registry.all_commands()/门数=core.GATE_ORDER/
字段=schemas.json 逐表列数和/金样面=run_golden 面清单），一律取 HEAD 提交态
（工作树在航件不污染口径；新命令落 commit 时快照红=计数同步义务入门槛）；
③活文档（cli/README.md/USAGE.md/SKILL.md）手抄命令/字段计数=生成值（禁第二份）。
另：cli/ 生产码禁第二份门枚举（"P5.5" 字面量只许 core.GATE_ORDER 一处——05 评审
「禁双份枚举从注释变机器」）。"""
import json, os, re, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DOCS = os.path.join(ROOT, "docs")
GEN = os.path.join(DOCS, "gen_counts.py")
COUNTS = os.path.join(DOCS, "counts.json")
LIVE_DOCS = ["cli/README.md", "USAGE.md", "SKILL.md"]


def _run_check():
    return subprocess.run([sys.executable, GEN, "--check"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestCountsSnapshot(unittest.TestCase):
    def test_check_passes_in_sync(self):
        self.assertTrue(os.path.isfile(GEN), "docs/gen_counts.py 生成器须在盘")
        r = _run_check()
        self.assertEqual(r.returncode, 0,
                         "counts.json 与单源派生漂移（rc=%d）：%s%s" % (r.returncode, r.stdout, r.stderr))

    def test_counts_json_shape(self):
        with open(COUNTS, encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["format_version"], 1)
        for k in ("ledger_commands", "ledger_gates", "ledger_fields", "golden_faces"):
            self.assertIsInstance(c[k], int, "计数键 %s 须为整数" % k)
        self.assertEqual(c["ledger_gates"], 9, "九门（GATE_ORDER 含 P5.5/P6.0）")


class TestSingleSourceDerivation(unittest.TestCase):
    """counts.json 值=HEAD 单源派生（生成器 collect() 独立复算，两端一致才算数）。"""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, DOCS)
        import gen_counts  # noqa: E402
        cls.gen = gen_counts

    def test_derived_matches_committed(self):
        with open(COUNTS, encoding="utf-8") as f:
            committed = json.load(f)
        derived = self.gen.collect()
        self.assertEqual(derived, committed,
                         "collect() 派生值与在册 counts.json 不一致：%r vs %r" % (derived, committed))

    def test_command_count_is_registry_truth(self):
        # 独立通道复算：HEAD 物化树里纯 registry 导入的命令面计数
        n = self.gen._head_face_count()
        with open(COUNTS, encoding="utf-8") as f:
            self.assertEqual(n, json.load(f)["ledger_commands"])


class TestLiveDocCounts(unittest.TestCase):
    """活文档手抄计数=生成值（41/44/49 三数并存病史的机械防线；历史档/设计档豁免）。"""

    def test_live_docs_command_and_field_counts(self):
        with open(COUNTS, encoding="utf-8") as f:
            c = json.load(f)
        for rel in LIVE_DOCS:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                text = f.read()
            cmds = {int(m) for m in re.findall(r"(\d+)\s*命令", text)}
            cmds |= {int(m) for m in re.findall(r"(\d+)\s*条账本命令", text)}
            cmds |= {int(m) for m in re.findall(r"命令索引（(\d+)\s*条", text)}
            self.assertTrue(cmds, "%s 须载命令面计数（或改指 docs/counts.json）" % rel)
            bad = cmds - {c["ledger_commands"]}
            self.assertFalse(bad, "%s 手抄命令计数过期 %s（单源=%d）" % (rel, sorted(bad), c["ledger_commands"]))
            fields = {int(m) for m in re.findall(r"(\d+)\s*字段", text)}
            badf = fields - {c["ledger_fields"]}
            self.assertFalse(badf, "%s 手抄字段计数过期 %s（单源=%d）" % (rel, sorted(badf), c["ledger_fields"]))


class TestNoSecondGateEnumeration(unittest.TestCase):
    def test_cli_py_has_no_gate_literal_outside_core(self):
        hits = []
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "cli")):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dirpath, fn)
                if fn == "core.py":
                    continue  # GATE_ORDER 单源本体
                with open(p, encoding="utf-8", errors="replace") as f:
                    for i, ln in enumerate(f, 1):
                        if '"P5.5"' in ln:
                            hits.append("%s:%d" % (os.path.relpath(p, ROOT), i))
        self.assertFalse(hits, "cli/ 生产码禁第二份门枚举（P5.5 字面量只许 core.py）：%s" % hits)


if __name__ == "__main__":
    unittest.main()
