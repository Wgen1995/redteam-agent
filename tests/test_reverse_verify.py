# -*- coding: utf-8 -*-
"""批次5 T15：反向验证落地（tanyin-redact --reverse-verify）+ CLIENT-NN 映射。

R13：phases.yaml P6 断言文本零改（`tanyin-redact --reverse-verify`）——实现在
special.h_reverse_verify（敏感词集=assets.value 全集+creds.username_ref+泄漏形态），
phases_engine 断言回路拆 EXTRA_TOOLS（report 留 ENV-HALT/redact 分发）；P6 门端到端首通。
R12：client-map next/add/list（运行时文件 client-map.tsv，真值永不进仓）。
退出码对齐 Strix：0=零命中 1=命中清单 2=用法/环境。
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))

REDACT = os.path.join(ROOT, "cli", "tanyin-redact")
KN = os.path.join(ROOT, "cli", "tanyin-knowledge")
PHASES = os.path.join(ROOT, "cli", "tanyin-phases")
FIX = os.path.join(HERE, "fixtures", "G-g1")
TS = "2026-09-24T13:00:00Z"
CLEAN = "结论：CLIENT-01 的管理面板存在越权（{{vault:cred-2}} 对照）。\n"


def run_redact(gd, *args):
    return subprocess.run([sys.executable, REDACT, "--goal-dir", gd] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def kn(*args):
    return subprocess.run([sys.executable, KN] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


class TestReverseVerify(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.d = shutil.copytree(FIX, os.path.join(self.td.name, "G-g1"))

    def _write_draft(self, text, rel=None):
        p = os.path.join(self.d, rel or os.path.join("report", "report-draft.md"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    # ------------------------------------------------------------- 反向验证

    def test_dirty_draft_detected(self):
        # 草稿含 assets.value 值 shop.example（session 出现过）→ exit 1 命中清单
        self._write_draft("结论：shop.example 的管理面板存在越权。\n")
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 1)
        self.assertIn("shop.example", r.stdout)
        self.assertIn("FAIL", r.stdout)
        self.assertRegex(r.stdout, r"report-draft\.md:1:")

    def test_clean_draft_zero_hits(self):
        # 净草稿：CLIENT-NN 占位+vault 凭据占位符（脱敏正当形态）→ exit 0 零命中
        self._write_draft(CLEAN)
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("零命中", r.stdout)

    def test_default_target_and_override(self):
        # 缺省 target=report/report-draft.md：不存在 → exit 2 环境问题
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 2)
        self.assertIn("草稿不存在", r.stderr)
        # --target 任意路径覆盖
        self._write_draft("结论：CLIENT-01 的管理面板存在越权。\n", "out/draft-r2.md")
        r2 = run_redact(self.d, "--reverse-verify", "--target=out/draft-r2.md")
        self.assertEqual(r2.returncode, 0, r2.stdout)
        self._write_draft("vpn.shop.example 泄漏。\n", "out/draft-r2.md")
        r3 = run_redact(self.d, "--reverse-verify", "--target=out/draft-r2.md")
        self.assertEqual(r3.returncode, 1)
        self.assertIn("vpn.shop.example", r3.stdout)

    def test_pattern_shape_hits(self):
        # 形态级通道：token 赋值形态（非资产值/账号名）→ 命中清单带 泄漏形态
        self._write_draft("配置 token=abcdef1234567890abcd 已复用。\n")
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 1)
        self.assertIn("泄漏形态", r.stdout)

    def test_username_ref_in_sensitive_words(self):
        # creds.username_ref（admin）入敏感词集——草稿出现即命中
        self._write_draft("以 admin 身份登录后台。\n")
        r = run_redact(self.d, "--reverse-verify")
        self.assertEqual(r.returncode, 1)
        self.assertIn("admin", r.stdout)

    def test_bad_usage_exit_2(self):
        r = run_redact(self.d, "--reverse-verify", "--bogus=1")
        self.assertEqual(r.returncode, 2)

    # ------------------------------------------------------------- gate P6 端到端

    def _seed_p6_prereq(self):
        from ledger import phases_engine as pe
        from ledger import write_cmds
        for ph in ("P4", "P5", "P5.5", "P6.0"):
            buf_o, buf_e = io.StringIO(), io.StringIO()
            with redirect_stdout(buf_o), redirect_stderr(buf_e):
                pe._append_event(self.d, ph,
                                 "gate-exit:%s asserts=1 result=PASS" % ph, TS)
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = write_cmds.HANDLERS["approve"](self.d, [
                "--command-hash=" + "a" * 64, "--decision=knowledge-approved",
                "--approver=人审", "--note=P6 沉淀审批", "--timestamp=" + TS])
        self.assertEqual(code, 0, buf_e.getvalue())

    def test_gate_p6_end_to_end(self):
        # 夹具补齐：P4-P6.0 前置门事件+approve --knowledge 行+净草稿 → P6 真跑 → END
        self._seed_p6_prereq()
        self._write_draft(CLEAN)
        r = subprocess.run([sys.executable, PHASES, "gate", "--goal-dir", self.d,
                            "--phase=P6", "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("gate:P6", r.stdout)
        self.assertIn("END", r.stdout, "P6 收官须落 END 态（on_pass=END）")

    def test_gate_p6_halt_on_dirty_draft(self):
        # 脏草稿 → P6 门 FAIL（exit 1=门禁失败，非 ENV-HALT）
        self._seed_p6_prereq()
        self._write_draft("结论：shop.example 存在越权。\n")
        r = subprocess.run([sys.executable, PHASES, "gate", "--goal-dir", self.d,
                            "--phase=P6", "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)

    def test_report_still_env_halt(self):
        # EXTRA_TOOLS 拆分半边：tanyin-report 维持 ENV-HALT（批次 6 交付）——
        # P5 前两断言链：terminal-gate（先清 web.api/inj.sql 空格）→ tanyin-report HALT
        from ledger import phases_engine as pe
        from ledger import registry
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            pe._append_event(self.d, "P4", "gate-exit:P4 asserts=1 result=PASS", TS)
            h = registry.lookup("matrix-set")
            code_ms = h(self.d, ["--attack-surface=web.api", "--vuln-class=inj.sql",
                                 "--state=-", "--reason=unreachable:外网不可达",
                                 "--timestamp=" + TS])
        self.assertEqual(code_ms, 0, buf_e.getvalue())
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.run_gate(self.d, "P5", TS, None)
        self.assertEqual(code, 2)
        self.assertIn("ENV-HALT", buf_o.getvalue())
        self.assertIn("tanyin-report", buf_o.getvalue())

    # ------------------------------------------------------------- CLIENT-NN 映射

    def test_client_map_cycle(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        self.assertEqual(kn("init", "--knowledge-dir=" + d).returncode, 0)
        r = kn("client-map", "--knowledge-dir=" + d, "next")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("CLIENT-01", r.stdout)
        r = kn("client-map", "--knowledge-dir=" + d, "add", "--client=CLIENT-01",
               "--real-ref=某零售客户", "--note=P6 首例", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r2 = kn("client-map", "--knowledge-dir=" + d, "next")
        self.assertIn("CLIENT-02", r2.stdout)
        rl = kn("client-map", "--knowledge-dir=" + d, "list")
        self.assertEqual(rl.returncode, 0, rl.stderr)
        self.assertIn("CLIENT-01", rl.stdout)
        self.assertIn("某零售客户", rl.stdout)

    def test_client_map_add_rejects_bad_shape_and_dup(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        kn("init", "--knowledge-dir=" + d)
        r = kn("client-map", "--knowledge-dir=" + d, "add", "--client=ACME",
               "--real-ref=x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1, "非 CLIENT-NN 形态须 REJECT")
        kn("client-map", "--knowledge-dir=" + d, "add", "--client=CLIENT-01",
           "--real-ref=x", "--timestamp=" + TS)
        r2 = kn("client-map", "--knowledge-dir=" + d, "add", "--client=CLIENT-01",
                "--real-ref=y", "--timestamp=" + TS)
        self.assertEqual(r2.returncode, 1, "重复 client 须 REJECT")

    def test_client_map_add_requires_timestamp(self):
        # G-23 同律：落 assigned_at 的时间戳显式传入，禁墙钟
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        kn("init", "--knowledge-dir=" + d)
        r = kn("client-map", "--knowledge-dir=" + d, "add", "--client=CLIENT-01",
               "--real-ref=x")
        self.assertEqual(r.returncode, 2)

    def test_client_map_example_template_in_seed(self):
        # R12：仓库种子只带 client-map.example.tsv 模板（真值 client-map.tsv 已 gitignore）
        p = os.path.join(ROOT, "knowledge", "client-map.example.tsv")
        self.assertTrue(os.path.isfile(p), "模板缺失")
        head = open(p, encoding="utf-8").readline().strip()
        self.assertEqual(head, "client\treal_ref\tnote\tassigned_at")

    def test_client_map_add_rejected_on_seed(self):
        # R7 种子库只读：client-map add 指向仓库 knowledge/ → REJECT exit 1
        r = kn("client-map", "--knowledge-dir=" + os.path.join(ROOT, "knowledge"),
               "add", "--client=CLIENT-01", "--real-ref=x", "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECT", r.stderr)


if __name__ == "__main__":
    unittest.main()
