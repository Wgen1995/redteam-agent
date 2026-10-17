# -*- coding: utf-8 -*-
"""W3-P1-1②③：deepex 派生层——读取类发现→凭据检查意图（不外发）+ RCE 取证模板。

P1-1「文件读取利用闭环:读到配置/密钥→add-cred(kind=session)→cred-obtained 事件→
身份差分自动触发（设计已全备,只差工具卡与技法页）」的引擎面第一段：读取类发现
（备份/配置文件）→凭据检查**意图卡**派生（总控落 intents，引擎不写账本）。
凭据材料**不外发**——检查=本地校验（格式/规则/重复使用），网络验证面不在本层。
"""
import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DERIVE = os.path.join(ROOT, "engines", "deepex", "derive.py")
FINDINGS = os.path.join(HERE, "fixtures", "engine", "deepex-findings.json")

sys.path.insert(0, os.path.join(ROOT, "engines", "deepex"))
import derive  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import enforce  # noqa: E402


class DeepexBase(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        with open(FINDINGS, encoding="utf-8") as f:
            self.findings = json.load(f)

    def by_dedup(self, findings, prefix):
        return [f for f in findings if f["dedup_key_proposed"].startswith(prefix)]


class TestCredIntentDerivation(DeepexBase):
    """② 读取类发现（备份/配置文件）→凭据检查意图派生。"""

    def test_backup_finding_derives_cred_intent(self):
        intents, _ = derive.derive_cred_intents(self.findings)
        src = self.by_dedup(self.findings, "/backup/db_backup.sql")
        hit = [i for i in intents if i["source_finding"] == src[0]["dedup_key_proposed"]]
        self.assertEqual(len(hit), 1, "备份文件发现须恰好派生一条凭据检查意图")
        it = hit[0]
        self.assertIn("凭据检查", it["title"])
        self.assertEqual(it["kind"], "deep-dive")
        self.assertEqual(it["origin"], "precedent")
        self.assertTrue(it["dedup_key_proposed"].endswith("+cred-check"))
        self.assertTrue(it["checks"], "检查计划非空")
        self.assertEqual(it["constraints"]["egress"], "forbidden",
                         "不外发=结构性约束，不是措辞自觉")

    def test_sensitive_file_patterns_covered(self):
        intents, _ = derive.derive_cred_intents(self.findings)
        srcs = {i["source_finding"] for i in intents}
        self.assertIn("/backup/db_backup.sql+fileread", srcs, "备份文件命中")
        self.assertIn("/app/.env+fileread", srcs, "配置文件命中")

    def test_non_read_finding_not_derived(self):
        intents, _ = derive.derive_cred_intents(self.findings)
        srcs = {i["source_finding"] for i in intents}
        self.assertNotIn("GET:id+sqlmap", srcs, "SQL注入发现不派生凭据检查")
        self.assertNotIn("/api/ping+rce", srcs, "RCE 发现走取证模板，不走凭据检查")

    def test_local_only_checks(self):
        intents, _ = derive.derive_cred_intents(self.findings)
        for it in intents:
            joined = " ".join(it["checks"])
            self.assertNotIn("http://", joined, "检查计划不得含网络面（不外发）")
            self.assertNotIn("https://", joined)
            self.assertIn("本地", joined, "每条检查显式标注本地")

    def test_no_secret_material_leaks_into_intent(self):
        """密值不进意图卡——源发现含 DB_PASSWORD=hunter2 也不带出。"""
        intents, _ = derive.derive_cred_intents(self.findings)
        blob = json.dumps(intents, ensure_ascii=False)
        self.assertNotIn("hunter2", blob)
        self.assertNotIn("sk-live-abc123", blob)

    def test_source_excerpt_redacted(self):
        intents, _ = derive.derive_cred_intents(self.findings)
        for it in intents:
            for val in (it.get("source_excerpt", ""),):
                self.assertNotIn("hunter2", val)
                self.assertNotIn("sk-live-abc123", val)

    def test_dedup_on_repeated_findings(self):
        doubled = self.findings + [f for f in self.findings
                                   if f["dedup_key_proposed"].startswith("/backup")]
        intents, _ = derive.derive_cred_intents(doubled)
        keys = [i["dedup_key_proposed"] for i in intents]
        self.assertEqual(len(keys), len(set(keys)), "同源发现重复出现只派生一次")

    def test_empty_and_none_inputs(self):
        self.assertEqual(derive.derive_cred_intents([])[0], [])
        self.assertEqual(derive.derive_cred_intents(None)[0], [])

    def test_malformed_finding_rows_tolerated(self):
        intents, skipped = derive.derive_cred_intents(
            [{"title": "备份文件 /x.bak"}, {"no_dedup": True}])
        self.assertEqual(intents, [], "缺 dedup 键的行跳过不崩")
        self.assertGreaterEqual(skipped, 1)


class TestCredIntentCLI(DeepexBase):
    """CLI 面：findings 文件→artifacts/derived-cred-intents.json（落 submissions 布局）。"""

    def run_cli(self):
        return subprocess.run(
            [sys.executable, DERIVE, "--findings-file", FINDINGS, "--out-dir", self.out],
            capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_cli_writes_artifact(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p = os.path.join(self.out, "artifacts", "derived-cred-intents.json")
        self.assertTrue(os.path.isfile(p), "产物落 artifacts/（契约 07 §1 布局）")
        doc = json.load(open(p, encoding="utf-8"))
        self.assertEqual(len(doc["intents"]), 2)
        self.assertIn("OK", r.stdout)

    def test_cli_deterministic_output(self):
        self.run_cli()
        first = open(os.path.join(self.out, "artifacts", "derived-cred-intents.json"),
                     "rb").read()
        out2 = tempfile.mkdtemp()
        subprocess.run([sys.executable, DERIVE, "--findings-file", FINDINGS,
                        "--out-dir", out2], capture_output=True)
        second = open(os.path.join(out2, "artifacts", "derived-cred-intents.json"),
                      "rb").read()
        self.assertEqual(first, second, "同输入同产物（无时戳/随机——金样可重放）")

    def test_cli_operations_log(self):
        self.run_cli()
        log = os.path.join(self.out, "operations.log")
        self.assertTrue(os.path.isfile(log))
        self.assertIn("cred-intents", open(log, encoding="utf-8").read())


class TestForensicTemplate(DeepexBase):
    """③ RCE 取证模板：命令执行类发现→取证包（非破坏三连+证据卡），禁删改。"""

    def rce(self):
        return self.by_dedup(self.findings, "/api/ping")[0]

    def test_trio_is_fixed_non_destructive(self):
        self.assertEqual(derive.FORENSIC_TRIO, ("whoami", "id", "hostname"),
                         "非破坏三连固定序，禁增删")

    def test_rce_finding_triggers_package(self):
        pkgs = derive.forensic_packages(self.findings)
        hit = [p for p in pkgs if p["source_finding"] == "/api/ping+rce"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(tuple(hit[0]["commands"]), derive.FORENSIC_TRIO)
        self.assertTrue(hit[0]["immutable"], "模板不可变标记（消费面禁改）")

    def test_non_rce_findings_no_package(self):
        pkgs = derive.forensic_packages(self.findings)
        srcs = {p["source_finding"] for p in pkgs}
        self.assertNotIn("GET:id+sqlmap", srcs)
        self.assertNotIn("/backup/db_backup.sql+fileread", srcs)

    def test_trio_passes_guard_denylist(self):
        """黑名单兼容：三连逐条过 guard deny 机械（原形+归一形+sh 包装形全过）。"""
        for c in derive.FORENSIC_TRIO:
            for form in enforce.deny_forms([c]):
                self.assertIsNone(enforce.deny_hit(form), "deny 命中: %r ← %s" % (form, c))
            for form in enforce.deny_forms(["sh", "-c", c]):
                self.assertIsNone(enforce.deny_hit(form), "sh 包装 deny 命中: %r" % form)

    def test_extra_commands_rejected(self):
        """禁删改：模板不可追加——任何 extra（含破坏性）一律拒。"""
        with self.assertRaises(ValueError):
            derive.forensic_packages([self.rce()], extra=["rm -rf /"])
        with self.assertRaises(ValueError):
            derive.forensic_packages([self.rce()], extra=["whoami"])

    def test_destructive_input_never_reaches_commands(self):
        pkgs = derive.forensic_packages([dict(self.rce(), title="命令执行; rm -rf / 注入")])
        blob = json.dumps(pkgs, ensure_ascii=False)
        for p in pkgs:
            self.assertEqual(tuple(p["commands"]), derive.FORENSIC_TRIO,
                             "发现文本含破坏载荷也不改三连")
        self.assertNotIn("rm -rf", blob, "包体不回带破坏载荷原文")

    def test_evidence_cards_one_per_command(self):
        pkgs = derive.forensic_packages([self.rce()])
        cards = pkgs[0]["evidence_cards"]
        self.assertEqual(len(cards), 3, "一命令一证据卡（落账锚）")
        self.assertEqual([c["command"] for c in cards], list(derive.FORENSIC_TRIO))
        for c in cards:
            self.assertTrue(c["expected_matcher"]["matchers"])
            self.assertEqual(c["capture"], "stdout")
            self.assertEqual(c["redaction"], "vault-tokenize")

    def test_package_deterministic(self):
        a = derive.forensic_packages([self.rce()])
        b = derive.forensic_packages([self.rce()])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_empty_input(self):
        self.assertEqual(derive.forensic_packages([]), [])
        self.assertEqual(derive.forensic_packages(None), [])


class TestForensicCLI(DeepexBase):
    """CLI 面：同一发现流双产物——取证包落 artifacts/forensic-packages.json。"""

    def test_cli_writes_forensic_artifact(self):
        r = subprocess.run(
            [sys.executable, DERIVE, "--findings-file", FINDINGS, "--out-dir", self.out],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p = os.path.join(self.out, "artifacts", "forensic-packages.json")
        self.assertTrue(os.path.isfile(p))
        doc = json.load(open(p, encoding="utf-8"))
        self.assertEqual(doc["count"], 1, "恰一条 RCE 发现触发取证包")
        self.assertIn("forensic", open(os.path.join(self.out, "operations.log"),
                                       encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
