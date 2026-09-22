# -*- coding: utf-8 -*-
"""redact 注入样本拦截率套件（批次 2 T6）。

样本集 tests/injection_samples/：36 阳性（每件一行泄漏载体）+7 阴性对照。
三载体注入：findings.description_brief / E-index.raw_excerpt / report/<stem>.md，
两模式扫描：账本模式（--goal-dir）+ 报告文本模式（--target=report 目录）。

TDD 红→绿留痕（2026-09-23）：
  红：按任务口径「阳性 100% 检出」朴素断言首跑 → 14/36（38.9%），22 形态漏检；
  绿：漏检根因=批次 1 模式清单（cli/ledger/special.py PLAIN_PATTERNS：
      私钥头/AKIA/password|passwd 赋值/ghp_/sk- 连续字母数字 16+/xox[baprs]-/
      eyJ JWT/{{vault:}} 占位符）覆盖面有限。按任务纪律不修 special.py
      （批次 1 文件冻结），22 形态登记为探知项 → KNOWN_MISS 棘轮：
      ①不允许新增漏检（EXPECTED_DETECT 集合只增不减，回退即红）；
      ②不允许登记表过期（漏检形态一旦被检出→红，提示收缩登记表）。
阴性硬断言：两模式零误报（含 E-index.repro_command 白名单列占位符正例）。

定位语义：文本模式定位=<stem>.md:行:列（含样本文件名，归因断言依据）；
账本模式定位=表:行:列，按追加行号映射归因（本套件行号映射确定性可溯）。
注：withheld 降级语义（§8.4）不在本套件范围（tanyin-redact 批次 1 无该语义，
neg_bearer_word_masked 仅以 withheld 字样作阴性对照）。
"""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "injection_samples")
FIX = os.path.join(HERE, "fixtures", "G-g1")
REDACT = os.path.join(HERE, "..", "cli", "tanyin-redact")
PY = sys.executable
TAB = chr(9)

# ============ 拦截率登记表（对批次 1 PLAIN_PATTERNS 实证标定 2026-09-23） ============
# 已检出形态：14/36——JWT / AKIA / ghp_ / xox[baprs]-（xoxb/xoxp/xoxa）/
# PEM 私钥头（RSA/EC/PKCS#8/OPENSSH）/ password= / passwd: / 经典 sk- /
# {{vault:cred-N}} 白名单列外。
EXPECTED_DETECT = {
    "pos_bearer_jwt", "pos_aws_akia", "pos_github_ghp",
    "pos_slack_xoxb", "pos_slack_xoxp", "pos_slack_xoxa",
    "pos_pem_rsa", "pos_pem_ec", "pos_pem_generic", "pos_openssh_key",
    "pos_password_eq", "pos_passwd_colon", "pos_api_sk",
    "pos_vault_out_of_whitelist",
    # —— 批次 2 T6 扩模式后全检出（special.py +16 形态，2026-09-23）——
    "pos_cookie_phpsessid", "pos_cookie_session", "pos_setcookie_reflect",
    "pos_aws_secret_cfg", "pos_aws_secret_env", "pos_github_gho",
    "pos_github_ghs", "pos_glpat", "pos_np_netlify", "pos_dockercfg",
    "pos_mysql_conn", "pos_postgres_conn", "pos_mongo_conn", "pos_redis_conn",
    "pos_basic_auth", "pos_bearer_opaque", "pos_ntlm_hash", "pos_token_eq",
    "pos_api_key_eq", "pos_secret_eq", "pos_client_secret_eq", "pos_api_sk_proj",
}
# 批次 2 T6 扩模式（special.py PLAIN_PATTERNS +16 形态）后漏检清零。
KNOWN_MISS = {}
# 阴性中唯一不走 report.md/raw_excerpt 载体的样本：占位符仅注入白名单列
# E-index.repro_command（契约 01 §3.9 白名单），注入其它载体本身就是泄漏。
WHITELIST_NEG = "neg_vault_whitelisted"


def _read_sample(stem):
    with open(os.path.join(SAMPLES, stem + ".txt"), encoding="utf-8") as f:
        return f.read().rstrip(chr(10))


def _findings_row(idx, sample):
    cells = ["FD-t9-%04d" % idx, "INT-g1-0002", "注入载体描述", "C3", "中",
             "suspected", "", "inj-carrier-%d" % idx, "", "in_scope",
             sample, "step-%d" % idx, "AST-g1-0002", "", "",
             "findings-cards/FD-t9-%04d.md" % idx, "active", "2",
             "2026-09-23T09:00:00Z"]
    return TAB.join(cells)


def _eindex_row(idx, sample, in_repro=False):
    cells = ["EV-t9-%04d" % idx, "注入载体摘录", "command", "2026-09-23T09:00:00Z",
             "internet", "curl -s https://shop.example/", "single", "a" * 32,
             "b" * 32, "artifacts/none-%d" % idx,
             "evidence/EV-t9-%04d.md" % idx, "", "PG-g1-0001",
             sample, "2", "2026-09-23T09:00:00Z"]
    if in_repro:
        cells[5] = sample
        cells[13] = "响应摘录占位"
    return TAB.join(cells)


def _run_redact(goal_dir, target=None):
    cmd = [PY, REDACT, "--goal-dir", goal_dir]
    if target:
        cmd.append("--target=" + target)
    return subprocess.run(cmd, capture_output=True, text=True)


def _leak_locs(proc):
    """跳过 PASS/FAIL 汇总行，取泄漏定位首列。"""
    return [l.split(TAB)[0] for l in proc.stdout.splitlines() if TAB in l and ":" in l.split(TAB)[0]]


class RedactInjectionSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pos_stems = sorted(f[:-4] for f in os.listdir(SAMPLES)
                               if f.startswith("pos_") and f.endswith(".txt"))
        cls.neg_stems = sorted(f[:-4] for f in os.listdir(SAMPLES)
                               if f.startswith("neg_") and f.endswith(".txt"))
        cls.text_neg_stems = [s for s in cls.neg_stems if s != WHITELIST_NEG]
        cls.base = tempfile.mkdtemp()
        # —— 阳性 goal：36 样本 × 三载体 ——
        gd = os.path.join(cls.base, "G-pos")
        shutil.copytree(FIX, gd)
        rep = os.path.join(gd, "report")
        os.makedirs(rep)
        with open(os.path.join(gd, "findings.tsv"), encoding="utf-8") as f:
            cls.f_base = len([l for l in f.read().splitlines() if l.strip()])
        with open(os.path.join(gd, "E-index.tsv"), encoding="utf-8") as f:
            cls.e_base = len([l for l in f.read().splitlines() if l.strip()])
        with open(os.path.join(gd, "findings.tsv"), "a", encoding="utf-8") as f:
            for i, st in enumerate(cls.pos_stems, 1):
                f.write(_findings_row(i, _read_sample(st)) + chr(10))
        with open(os.path.join(gd, "E-index.tsv"), "a", encoding="utf-8") as f:
            for i, st in enumerate(cls.pos_stems, 1):
                f.write(_eindex_row(i, _read_sample(st)) + chr(10))
        for st in cls.pos_stems:
            with open(os.path.join(rep, st + ".md"), "w", encoding="utf-8") as f:
                f.write(_read_sample(st) + chr(10))
        cls.pos_table = _run_redact(gd)
        cls.pos_text = _run_redact(gd, rep)
        # —— 阴性 goal：对照 + 白名单列正例 ——
        gd2 = os.path.join(cls.base, "G-neg")
        shutil.copytree(FIX, gd2)
        rep2 = os.path.join(gd2, "report")
        os.makedirs(rep2)
        with open(os.path.join(gd2, "findings.tsv"), "a", encoding="utf-8") as f:
            for i, st in enumerate(cls.text_neg_stems, 1):
                f.write(_findings_row(i, _read_sample(st)) + chr(10))
        with open(os.path.join(gd2, "E-index.tsv"), "a", encoding="utf-8") as f:
            for i, st in enumerate(cls.text_neg_stems, 1):
                f.write(_eindex_row(i, _read_sample(st)) + chr(10))
            f.write(_eindex_row(99, _read_sample(WHITELIST_NEG), in_repro=True) + chr(10))
        for st in cls.text_neg_stems:
            with open(os.path.join(rep2, st + ".md"), "w", encoding="utf-8") as f:
                f.write(_read_sample(st) + chr(10))
        cls.neg_table = _run_redact(gd2)
        cls.neg_text = _run_redact(gd2, rep2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    # ---------- 样本集卫生 ----------
    def test_01_sample_set_hygiene(self):
        self.assertGreaterEqual(len(self.pos_stems), 32, "阳性样本 <32")
        self.assertGreaterEqual(len(self.neg_stems), 5, "阴性对照 <5")
        disk = set(self.pos_stems)
        self.assertEqual(disk, EXPECTED_DETECT | set(KNOWN_MISS),
                         "登记表与样本文件集不一致（新增/删除样本必须同步登记表）")
        for stem in self.pos_stems + self.neg_stems:
            with open(os.path.join(SAMPLES, stem + ".txt"), encoding="utf-8") as f:
                raw = f.read()
            self.assertTrue(raw.endswith(chr(10)), stem + " 须 LF 结尾")
            body = raw[:-1]
            self.assertEqual(body.count(chr(10)), 0, stem + " 必须单行")
            self.assertTrue(body.strip(), stem + " 不得为空行")
            self.assertNotIn(TAB, body, stem + " 不得含 tab")
            self.assertNotIn("\r", body, stem + " 不得含 CR")

    # ---------- 阳性·文本模式：检出集合棘轮 + 文件名归因 ----------
    def test_02_positive_text_mode(self):
        self.assertEqual(self.pos_text.returncode, 1, "阳性文本模式须 FAIL(leaks>0)")
        det = {l.split(":")[0][:-3] for l in _leak_locs(self.pos_text)}
        self.assertEqual(det, EXPECTED_DETECT,
                         "文本模式检出集合≠登记表：新增漏检=%s / 登记表过期=%s"
                         % (sorted(EXPECTED_DETECT - det), sorted(det - EXPECTED_DETECT)))
        for stem in det:
            self.assertTrue(any(stem + ".md" in l for l in _leak_locs(self.pos_text)),
                            stem + " 泄漏定位未含样本文件名")

    # ---------- 阳性·账本模式：检出集合棘轮 + 表:行:列定位 ----------
    def test_03_positive_table_mode(self):
        self.assertEqual(self.pos_table.returncode, 1, "阳性账本模式须 FAIL(leaks>0)")
        locs = _leak_locs(self.pos_table)
        det_fd = {self.pos_stems[int(l.split(":")[1]) - self.f_base - 1]
                  for l in locs if l.startswith("findings.tsv:")}
        det_ev = {self.pos_stems[int(l.split(":")[1]) - self.e_base - 1]
                  for l in locs if l.startswith("E-index.tsv:")}
        for name, det in (("findings", det_fd), ("E-index", det_ev)):
            self.assertEqual(det, EXPECTED_DETECT,
                             "%s 载体检出集合≠登记表：新增漏检=%s / 登记表过期=%s"
                             % (name, sorted(EXPECTED_DETECT - det), sorted(det - EXPECTED_DETECT)))
        for i, stem in enumerate(self.pos_stems, 1):
            if stem not in EXPECTED_DETECT:
                continue
            f_ln, e_ln = self.f_base + i, self.e_base + i
            self.assertIn("findings.tsv:%d:description_brief" % f_ln, locs,
                          stem + " 须定位 findings.tsv:%d:description_brief" % f_ln)
            self.assertIn("E-index.tsv:%d:raw_excerpt" % e_ln, locs,
                          stem + " 须定位 E-index.tsv:%d:raw_excerpt" % e_ln)

    # ---------- 阴性：两模式零误报（含白名单列正例） ----------
    def test_04_negative_zero_false_positives(self):
        self.assertEqual(self.neg_table.returncode, 0,
                         "阴性账本模式误报：" + self.neg_table.stdout)
        self.assertTrue(self.neg_table.stdout.startswith("PASS" + TAB + "leaks=0"))
        self.assertEqual(self.neg_text.returncode, 0,
                         "阴性文本模式误报：" + self.neg_text.stdout)
        self.assertTrue(self.neg_text.stdout.startswith("PASS" + TAB + "leaks=0"))
        with open(os.path.join(SAMPLES, WHITELIST_NEG + ".txt"), encoding="utf-8") as f:
            wl = f.read().rstrip(chr(10))
        self.assertIn("{{vault:cred-1}}", wl, "白名单列正例载体缺失")
        gd2 = os.path.join(self.base, "G-neg")
        with open(os.path.join(gd2, "E-index.tsv"), encoding="utf-8") as f:
            rows = [r.split(TAB) for r in f.read().splitlines() if r.strip()]
        wl_rows = [r for r in rows if r[5] == wl]
        self.assertEqual(len(wl_rows), 1, "白名单正例须落在 repro_command 列")

    # ---------- 拦截率汇总（探知项输出位） ----------
    def test_05_interception_rate_summary(self):
        det_text = {l.split(":")[0][:-3] for l in _leak_locs(self.pos_text)}
        det_fd = {self.pos_stems[int(l.split(":")[1]) - self.f_base - 1]
                  for l in _leak_locs(self.pos_table) if l.startswith("findings.tsv:")}
        self.assertEqual(det_text, det_fd, "文本/账本两模式检出集合须一致")
        total, hit = len(self.pos_stems), len(EXPECTED_DETECT)
        self.assertEqual(hit + len(KNOWN_MISS), total, "登记表未全覆盖样本")
        missed = "、".join(KNOWN_MISS[s] for s in sorted(KNOWN_MISS))
        print("拦截率汇总: %d/%d（%.1f%%） 阳性=%d 阴性=%d 误报=0 漏检=%d"
              % (hit, total, hit * 100.0 / total, total, len(self.neg_stems), len(KNOWN_MISS)))
        print("漏检形态（探知项）: " + missed)


if __name__ == "__main__":
    unittest.main()
