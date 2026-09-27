# -*- coding: utf-8 -*-
"""批次6 T17：budget-exhausted 终态 B（合法签发终态+中期披露强制）+演练前置证据链。

夹具=G-g1 复制+CLI 铸造（T14 同款 _mint；预算抽干经 budget-log 真命令追加
budget.tsv 行+budgetctl enforce REJECT 落账=终态 B 前置证据链，R-T14-1 豁免同律）；
时间戳全字面量。终态 B 语义（契约 13 勘误，T17 兑现）：budget-exhausted=合法签发
终态，报告强制含「中期报告声明+未测范围披露清单」（gaps 逐格，铁律 3 诚实覆盖口径）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import report_lint  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402
from tests.test_report_lint import repair_auth  # noqa: E402  批次 7 T8 夹具修补单源

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
BUDGETCTL = os.path.join(ROOT, "cli", "tanyin-budgetctl")
TS = "2026-09-24T09:00:00Z"
EV_ID = "EV-g1-0002"
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


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mint(self):
        """CLI 铸 EV+FD+豁免行（T14 test_report_lint 同款——签发门其余门可过）；
        批次 7 T8 起随铸授权三件套修补（签发授权门接线，补夹具不放水）。"""
        gd = self.gd
        repair_auth(gd)
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

    def _copy_g1_with_budget_exhausted(self):
        """CLI 铸造：budget-log 真命令追加至 token 维穿限+budgetctl enforce REJECT 落账。

        夹具根预算 token=2M、已耗 20000（goal 12000+INT 8000）——追加 1 990 000 使
        used=2 011 000>2 000 000（query_cmds.budget_exhausted 判穿）；enforce 随即
        REJECT（used>=lim，零余量即拒派）并落 budgetctl-reject 事件=终态 B 证据链。"""
        self._mint()
        gd = self.gd
        r = run(LEDGER, "budget-log", "--goal-dir", gd,
                "--token-delta=1990000", "--requests-delta=0", "--hours-delta=0",
                "--scope=goal", "--note=T17 演练抽干（token 维穿限）",
                "--timestamp=2026-09-23T05:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(BUDGETCTL, "enforce", "--goal-dir", gd, "--intent-id=INT-g1-0002",
                "--timestamp=2026-09-23T06:00:00Z")
        self.assertEqual(r.returncode, 1, "预算穿限后 enforce 须 REJECT rc=1")
        self.assertIn("budget-exhausted", r.stdout)
        return gd

    def _signed_report(self, gd):
        with open(os.path.join(gd, "report", "signed", "interim-report.md"),
                  encoding="utf-8") as f:
            return f.read()


def _strip_limits_projection(gd):
    """反例夹具：抽掉披露数据——矩阵空格全填使 gaps 清空，中期披露清单失据。"""
    p = os.path.join(gd, "matrix.tsv")
    cols = TABLES["matrix.tsv"]
    si = cols.index("state")
    with open(p, encoding="utf-8") as f:
        rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    for r in rows:
        if not r[si].strip():
            r[si] = "na"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join("\t".join(r) + "\n" for r in rows))


class TestTerminalB(Base):
    def test_exhausted_passes_gate_with_disclosure(self):
        gd = self._copy_g1_with_budget_exhausted()
        rc, rep = report_lint.sign_gate(gd, TS)
        self.assertEqual(rc, 0, rep)                    # 终态 B 可签发
        md = self._signed_report(gd)
        self.assertIn("中期报告", md)
        self.assertIn("未测范围披露", md)
        # 契约 13 §3 budget-exhausted 强制披露四件套（逐格清单/未跑 intent/闭合率/免责）
        self.assertIn("web.api/inj.sql", md)            # gaps 逐格列出
        self.assertIn("INT-g1-0002", md)                # 未跑 intent 清单
        self.assertIn("闭合率", md)
        self.assertIn("免责", md)

    def test_exhausted_without_disclosure_fails(self):
        gd = self._copy_g1_with_budget_exhausted()
        _strip_limits_projection(gd)                    # 反例：抽掉披露数据（gaps 清空）
        rc, rep = report_lint.sign_gate(gd, TS)
        self.assertEqual(report_lint.sign_gate(gd, TS)[0], 1)
        self.assertIn("未测矩阵格清单", str(rep))

    def test_budget_reject_event_in_timeline(self):
        # 预算超限 REJECT 落账断言（既有 budgetctl 面复核——终态 B 的前置证据链）
        gd = self._copy_g1_with_budget_exhausted()
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("budgetctl-reject", tl)
        self.assertIn('"mode":"enforce"', tl)      # REJECT 明细（budget-exhausted 字样在 enforce stdout）
        self.assertIn('"level":"goal"', tl)
        self.assertIn("budget-log goal", tl)


class TestTerminalBNormal(unittest.TestCase):
    def test_normal_terminal_no_interim(self):
        """终态 A（normal）不产中期报告——支线语义只在 exhausted 分支生效。"""
        import json
        self.assertFalse(os.path.exists(os.path.join(
            FIX, "report", "signed", "interim-report.md")),
            "共享夹具零触碰：interim 支线不得写共享夹具")


if __name__ == "__main__":
    unittest.main()
