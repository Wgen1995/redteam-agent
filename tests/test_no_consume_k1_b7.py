# -*- coding: utf-8 -*-
"""批次 7 T13：触发器显式不消费通道（High：无通道逼假边——新增 fact 后
converge=running 无出清，审计 FAIL 逼伪造消费边）+K1 缺基线 exit 2
（High：severity 0.9→0.5 静默降级仅 stdout warnings、rc=0）。

裁决（R-T13，详见 HANDOFF）：标记语义=facts.detail 单元格追加 [no-consume:<理由>]
——facts.tsv 无 note 列且 13 表列集冻结（Global Constraints），detail 为自由文本
唯一承载位；消费执法面（unconsumed-facts 计数/trigger-audit deferred 计数）跳过
带标记事实并单列 deferred=<n>（n>0 才出列=金样零漂移）；缺基线文件=KnowledgeEnvError
（环境域 exit 2），基线文件在、缺 vuln_class 行=合法缺省（warning+0.5）——两态分流。
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import knowledge
from tests.test_dryrun_p0p2 import fresh_drydir, ledger, phases, TS

LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
TAB = chr(9)
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
FIX = os.path.join(HERE, "fixtures", "G-g1")
SEED = os.path.join(ROOT, "knowledge")

FACT_KEYS = ["--intent-id=INT-g1-0001", "--kind=info", "--confidence=0.9"]


def _g1_copy(td, name):
    gd = os.path.join(td, name)
    shutil.copytree(FIX, gd)
    return gd


def _kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class TestNoConsume(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = _g1_copy(self.td.name, "G-nc")
        # ④高危横向机检基线（test_trigger_audit setUp 同款纪律）：基线 FD-g1-0001 披露 fact
        rc, out, err = ledger(self.gd, "add-fact", ["--intent-id=INT-g1-0001", "--kind=info",
                              "--target=lateral:FD-g1-0001", "--detail=披露：高危 finding 轮内已横向排查",
                              "--confidence=0.9", "--timestamp=" + TS])
        assert rc == 0, out + err

    def _add_fact(self, gd, extra):
        return subprocess.run([sys.executable, LEDGER, "add-fact", "--goal-dir", gd]
                              + FACT_KEYS + extra, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def _unconsumed_count(self, gd):
        rc, out, err = ledger(gd, "unconsumed-facts")
        self.assertEqual(rc, 0, out + err)
        n = None
        for ln in out.splitlines():
            if ln.startswith("#count="):
                n = int(ln.split("=", 1)[1])
        self.assertIsNotNone(n, "unconsumed-facts 输出无 #count 行: " + out)
        return n

    def test_no_consume_requires_reason(self):
        """理由空=usage exit 2（防无意识标记；红期如实录：未知参数亦 usage 2，
        本例钉死契约形——绿后语义=参数存在但空值 Usage）。"""
        r = self._add_fact(self.gd, ["--target=x", "--detail=d",
                                     "--no-consume=", "--timestamp=" + TS])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("no-consume", r.stderr, "拒绝消息须点名 no-consume 通道")

    def test_marker_lands_in_fact_row(self):
        r = self._add_fact(self.gd, ["--target=x", "--detail=d",
                                     "--no-consume=界外情报仅记录", "--timestamp=" + TS])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(self.gd, "facts.tsv"), encoding="utf-8") as f:
            facts = f.read()
        self.assertIn("[no-consume:界外情报仅记录]", facts, "标记须落在 fact 行（detail 承载位）")

    def test_marked_fact_skips_unconsumed_and_counts_deferred(self):
        """红=同一「未消费 fact」无通道只增不减（converge=running 无出清）；
        绿=标记后退出未消费清单+deferred=<n> 单列。"""
        n0 = self._unconsumed_count(self.gd)
        r1 = self._add_fact(self.gd, ["--target=x", "--detail=普通未消费",
                                      "--timestamp=" + TS])
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        rc, out, err = ledger(self.gd, "unconsumed-facts")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self._unconsumed_count(self.gd), n0 + 1,
                         "普通 fact 仍入未消费清单（执法不松动）")
        self.assertNotIn("deferred=", out, "零标记时不出 deferred 列（金样零漂移口径）")
        r2 = self._add_fact(self.gd, ["--target=y", "--detail=界外线索",
                                      "--no-consume=错误线索不追", "--timestamp=" + TS])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        rc, out, err = ledger(self.gd, "unconsumed-facts")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self._unconsumed_count(self.gd), n0 + 1,
                         "标记 fact 退出未消费清单（显式不消费=合法出清通道）")
        self.assertIn("deferred=1", out, "显式不消费单列计数")

    def test_trigger_audit_marked_deferred_fact_closes_and_counts(self):
        """红=专家反例：cred-obtained 触发器「应消费事实」无显式不消费通道——
        审计 FAIL 逼伪造消费边；绿=带标记延后 fact 过审+deferred=<n>。"""
        rc, out, err = ledger(self.gd, "add-cred", ["--kind=session", "--role=operator",
                              "--username-ref=op9", "--secret-ref={{vault:cred-2}}",
                              "--parent-cred=CRED-g1-0001", "--timestamp=" + TS])
        self.assertEqual(rc, 0, out + err)
        cid = out.split(TAB)[1]  # OK<CID>creds.tsv——id 随 goal-id 前缀 mint，禁手抄
        rc, out, err = phases(self.gd, "trigger-audit")
        self.assertEqual(rc, 1, "红现状：无通道时审计 FAIL（逼假边）: " + out + err)
        self.assertIn("authz-diff", out + err)
        r = self._add_fact(self.gd, ["--target=authz-diff:" + cid,
                                     "--detail=错误线索显式不追",
                                     "--no-consume=错误线索不追", "--timestamp=" + TS])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rc, out, err = phases(self.gd, "trigger-audit")
        self.assertEqual(rc, 0, "显式不消费=合法闭合，审计放行: " + out + err)
        self.assertIn("deferred=1", out, "审计 PASS 行单列 deferred 计数")


class TestK1BaselineEnv(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def test_score_missing_baseline_raises(self):
        """基线文件缺=方法库未安装（环境问题域）→ KnowledgeEnvError。"""
        with self.assertRaises(knowledge.KnowledgeEnvError):
            knowledge.score(os.path.join(self.td.name, "kb"),
                            os.path.join(self.td.name, "g"),
                            "wstg-info", "asset", "2026-09-27")

    def test_consumer_exit_2_on_missing_baseline(self):
        """红=专家实测：缺基线 severity 0.9→0.5 静默降级仅 warnings、rc=0；
        绿=消费者 stderr 提示 K1+exit 2。"""
        kb = os.path.join(self.td.name, "kb")
        shutil.copytree(SEED, kb)
        os.remove(os.path.join(kb, "methodology", "k1-baseline.tsv"))
        gd = _g1_copy(self.td.name, "G-k1")
        r = _kn("score", "--knowledge-dir=" + kb, "--goal-dir=" + gd,
                "--vuln-class=wstg-authz", "--asset=AST-g1-0002", "--today=2026-09-24")
        self.assertEqual(r.returncode, 2, "红现状：缺基线静默降级 rc=0: " + r.stdout)
        self.assertIn("K1", r.stderr, "stderr 须点名 K1 基线缺失")

    def test_missing_row_still_warns_default(self):
        """裁决对照例（两态分流）：基线文件在、缺 vuln_class 键=合法缺省
        （查表 warning+0.5），不得误杀为环境错。"""
        sev, key, warns = knowledge.baseline_lookup(SEED, "wstg-other")
        self.assertEqual(sev, 0.5)
        self.assertEqual(key, "")
        self.assertTrue(warns, "缺行仍须查表告警")
        gd = _g1_copy(self.td.name, "G-k1b")
        r = _kn("score", "--knowledge-dir=" + SEED, "--goal-dir=" + gd,
                "--vuln-class=wstg-other", "--asset=AST-g1-0002", "--today=2026-09-24")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["severity_expect"], 0.5)
        self.assertTrue(out["sources"]["warnings"], "score 输出面 warning 仍在")


if __name__ == "__main__":
    unittest.main()
