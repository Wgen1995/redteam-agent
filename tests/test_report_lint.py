# -*- coding: utf-8 -*-
"""批次6 T14：G-25 Burp 直贴 lint（裁决 B 四规则+双指纹）+P5 签发门+P6 清理门接线。

夹具=G-g1 复制+CLI 铸造（T13 同款 mint；豁免行经 approve --decision=exempted 铸造——
夹具首行 add-goal revert_cmd=irreversible 需先豁免，签发门 cleanup 核销判定才可能 PASS）；
时间戳全字面量。P5 解除=phases_engine 分发真门（tanyin-redact R13 拆分同构）。"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import phases_engine as pe  # noqa: E402
from ledger import report_agg, report_lint, report_render, selfcheck  # noqa: E402
from ledger import registry  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")
TS = "2026-09-24T09:00:00Z"
EV_ID, FD_ID = "EV-g1-0002", "FD-g1-0002"
RAW_REQUEST = "GET /admin/orders HTTP/1.1\nHost: admin-internal.shop.example\nAccept: */*"
CARD_TEXT = ("---\nid: %s\ntitle: admin 面板匿名可读-实验组\nsource_type: capture\n"
             % EV_ID
             + "observed_at: 2026-09-23T02:30:00Z\nnetwork_position: intranet\n"
             + "preconditions:\n  - 可解析 admin-internal.shop.example（DNS 内网视角）\n"
             + "raw_request: |\n  GET /admin/orders HTTP/1.1\n"
             + "  Host: admin-internal.shop.example\n  Accept: */*\n"
             + "expected: {}\ncleanup: ''\npair_group: \nrole: \n---\n"
             + "## 原始响应摘录（脱敏+定长）与判定依据\n"
             + "HTTP/1.1 200 OK（脱敏样例：未登录可读订单列表，token 化后原文）\n")


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class TestBurpLint(unittest.TestCase):
    RAW = ("POST /login HTTP/1.1\r\nHost: t.example.com\r\n"
           + "Content-Type: application/x-www-form-urlencoded\r\n\r\nuser=a&pass=b")

    def test_happy_path(self):
        ok, why = report_lint.burp_pasteable(self.RAW)
        self.assertTrue(ok, why)

    def test_missing_host(self):
        bad = self.RAW.replace("Host: t.example.com\r\n", "")
        self.assertFalse(report_lint.burp_pasteable(bad)[0])

    def test_bad_request_line(self):
        self.assertFalse(report_lint.burp_pasteable("POST /login\r\nHost: h\r\n\r\n")[0])

    def test_binary_bytes_rejected(self):
        self.assertFalse(report_lint.burp_pasteable("POST / HTTP/1.1\r\nHost: h\r\n\r\n\x00\x02frame")[0])

    def test_http2_frame_directed_to_note(self):
        ok, why = report_lint.burp_pasteable(
            "POST / HTTP/1.1\r\nHost: h\r\n\r\n[HTTP/2 binary frame: DATA]\x01\x02")
        self.assertFalse(ok)
        self.assertIn("判读说明", " ".join(why))

    def test_lf_only_accepted(self):
        ok, why = report_lint.burp_pasteable("GET / HTTP/1.1\nHost: h")
        self.assertTrue(ok, why)                      # LF 行尾跨平台直贴

    def test_body_without_separator_fail(self):
        ok, why = report_lint.burp_pasteable("POST / HTTP/1.1\r\nHost: h\r\nuser=a")
        self.assertFalse(ok)
        self.assertTrue(any("空行" in w for w in why))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mint(self):
        """CLI 铸 EV+FD+豁免行（T13 同款 mint；豁免=cleanup 核销判定前置）。"""
        gd = self.gd
        art = os.path.join(gd, "evidence", EV_ID + ".raw")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(RAW_REQUEST)
        r = run(LEDGER, "add-evidence", "--goal-dir", gd,
                "--title=admin 面板匿名可读-实验组", "--source-type=capture",
                "--observed-at=2026-09-23T02:30:00Z", "--network-position=intranet",
                "--repro-command=curl -s http://admin-internal.shop.example/admin/orders",
                "--repro-kind=single", "--artifact=evidence/" + EV_ID + ".raw",
                "--raw-excerpt=HTTP/1.1 200 OK 订单列表脱敏样例（token 化后）",
                "--timestamp=2026-09-23T02:35:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(gd, "evidence", EV_ID + ".md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(CARD_TEXT)
        r = run(LEDGER, "add-finding", "--goal-dir", gd,
                "--intent-id=INT-g1-0002", "--title=admin 面板匿名可读（复核样本）",
                "--confidence=C1", "--impact=高", "--exploitation-status=verified",
                "--scope-check=in_scope", "--description-brief=未登录可读订单列表（签发门夹具）",
                "--reproducible-steps=匿名 GET /admin/orders;响应 200 含订单列表",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=" + EV_ID,
                "--timestamp=2026-09-23T03:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(LEDGER, "approve", "--goal-dir", gd, "--command-hash=" + "b" * 64,
                "--decision=exempted", "--approver=客户",
                "--note=授权登记不可逆豁免 add-goal G-g1-0001",
                "--timestamp=2026-09-23T04:00:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestSignGate(Base):
    def test_gate_pass_on_fixture(self):
        self._mint()
        rc, rep = report_lint.sign_gate(self.gd, TS)
        self.assertEqual(rc, 0, rep)
        self.assertTrue(os.path.exists(os.path.join(self.gd, "report", "signed", "pass.json")))

    def test_gate_fail_missing_segment(self):
        self._mint()
        rc, _ = report_render.render_all(self.gd, os.path.join(self.gd, "report", "draft"))
        self.assertEqual(rc, 0)
        p = os.path.join(self.gd, "report", "draft", FD_ID + ".md")
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        head, _seg9 = txt.rsplit("## 复现与验证状态", 1)   # 夹具操作：删第 9 段再 lint
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(head)
        rc, rep = report_lint.sign_gate(self.gd, TS)
        self.assertEqual(rc, 1)
        self.assertIn("复现与验证状态", str(rep))

    def test_gate_fail_cleanup_not_verified(self):
        self._mint()
        r = run(LEDGER, "append-timeline", "--goal-dir", self.gd, "--actor=子代理",
                "--phase=P6.0", "--event=probe:demo", "--revert-cmd=undo-probe",
                "--timestamp=2026-09-23T05:00:00Z")   # 铸未核销副作用行
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rc, rep = report_lint.sign_gate(self.gd, TS)
        self.assertEqual(rc, 1)
        self.assertIn("cleanup", str(rep))

    def test_gate_fail_dual_fingerprint(self):
        self._mint()
        with open(os.path.join(self.gd, "evidence", EV_ID + ".raw"), "a",
                  encoding="utf-8", newline="\n") as f:
            f.write("\n")                              # 工件改一字
        rc, rep = report_lint.sign_gate(self.gd, TS)
        self.assertEqual(rc, 1)
        self.assertIn("指纹", str(rep))

    def test_lint_cli_no_credential_sign_writes(self):
        self._mint()
        cred = os.path.join(self.gd, "report", "signed", "pass.json")
        r = run(REPORT, "lint", "--goal-dir", self.gd, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(cred), "lint 不落签发凭证")
        r2 = run(REPORT, "sign", "--goal-dir", self.gd, "--timestamp=" + TS)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertTrue(os.path.exists(cred))
        self.assertIn("T15", r2.stdout)                # 双工件未接线的披露行

    def test_sign_requires_timestamp(self):
        r = run(REPORT, "sign", "--goal-dir", self.gd)
        self.assertEqual(r.returncode, 2)


class TestWiring(Base):
    def test_p5_note_updated(self):
        with open(os.path.join(ROOT, "phases", "P5.md"), encoding="utf-8") as f:
            txt = f.read()
        self.assertNotIn("批次 6 交付前该断言=ENV-HALT", txt)   # 解除兑现
        self.assertIn("tanyin-report lint", txt)
        with open(os.path.join(ROOT, "phases", "P6.md"), encoding="utf-8") as f:
            p6 = f.read()
        self.assertIn("cleanup-checklist --verify", p6)         # 清理门接线注记
        with open(os.path.join(ROOT, "contracts", "06-evidence-cards.md"), encoding="utf-8") as f:
            c06 = f.read()
        for kw in ("HTTP/1.x", "判读说明", "双指纹"):            # 裁决 B 三条款
            self.assertIn(kw, c06)
        self.assertIn("lint", selfcheck.KNOWN_COMMANDS["report"])

    def test_p5_assert_dispatches_report_lint(self):
        gd = self.gd
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            pe._append_event(gd, "P4", "gate-exit:P4 asserts=1 result=PASS", TS)
            h = registry.lookup("matrix-set")
            code_ms = h(gd, ["--attack-surface=web.api", "--vuln-class=inj.sql",
                             "--state=-", "--reason=unreachable:外网不可达",
                             "--timestamp=" + TS])
        self.assertEqual(code_ms, 0, buf_e.getvalue())
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = pe.run_gate(gd, "P5", TS, None)
        self.assertEqual(code, 1, buf_o.getvalue() + buf_e.getvalue())   # 真门 FAIL 非 HALT
        self.assertNotIn("ENV-HALT", buf_o.getvalue())
        self.assertIn("tanyin-report", buf_o.getvalue())


if __name__ == "__main__":
    unittest.main()
