# -*- coding: utf-8 -*-
"""批次 7 T8：签发授权完整性门（C5 反例三；台账 C5 行）。

红测=合规总监四绕专家反例复现（本文件 T8 先承载①③两绕）：
①sign_gate 零 approvals 校验——approvals.tsv 无 approved 行 sign 照发；
③goals.tsv auth_sha256=deadbeef+窗口 2020 过期 → verify-chain PASS、sign rc=0。
台账原文：「报告法律要件可绕：sign_gate 零 approvals 校验；draft C1→C3 手改直通；
goals sha256=deadbeef+窗口过期 verify-chain PASS、sign rc=0；脱敏扫描先于工件落盘」。

夹具=G-g1 拷贝+授权三件套修补（auth 文件+真 sha256 写 goals 拷贝）+CLI 铸造
→ sign 既有十一门全绿基线，再逐腿破坏=红反例（FAIL 归因唯一，其余门不背锅）。
共享夹具本体零触碰：金样 .state 引用夹具伪 sha（aaaa…），动本体=大面积金样漂移。
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import report_lint  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")
TS = "2026-09-24T09:00:00Z"   # 窗口 [2026-09-01, 2026-09-30] 之内（既有夹具签发时刻）
EV_ID, FD_ID = "EV-g1-0002", "FD-g1-0002"
AUTH_DOC_BYTES = b"AUTH-DOC-BYTES G-g1-0001\n"
DEAD = "d" * 64
RAW_REQUEST = ("GET /admin/orders HTTP/1.1\n"
               "Host: admin-internal.shop.example\n"
               "Accept: */*")
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


def _set_goals_cell(gd, col, val):
    """goals.tsv 拷贝内直写单格（原子写同形 tmp+os.replace，LF 纪律；本体零触碰）。"""
    p = os.path.join(gd, "goals.tsv")
    gi = TABLES["goals.tsv"].index
    with open(p, encoding="utf-8") as f:
        rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    rows[0][gi(col)] = val
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join("\t".join(r) + "\n" for r in rows))
    os.replace(tmp, p)


def _repair_auth(gd):
    """授权三件套修补（批次 7 T8 授权门接线后夹具补齐）：auth 文件落盘+真 sha256
    写 goals 拷贝（auth_doc=auth/G-g1-0001.pdf 列在夹具既有行）。"""
    authp = os.path.join(gd, "auth", "G-g1-0001.pdf")
    os.makedirs(os.path.dirname(authp), exist_ok=True)
    with open(authp, "wb") as f:
        f.write(AUTH_DOC_BYTES)
    with open(authp, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    _set_goals_cell(gd, "auth_sha256", real)


def _strip_approved(gd):
    """approvals.tsv 拷贝内剔除 decision=approved 行（专家反例①载体：零批准在案）。"""
    p = os.path.join(gd, "approvals.tsv")
    ai = TABLES["approvals.tsv"].index("decision")
    with open(p, encoding="utf-8") as f:
        rows = [ln for ln in f.read().splitlines(True) if ln.strip()]
    keep = [ln for ln in rows if ln.rstrip("\n").split("\t")[ai] != "approved"]
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(keep))
    os.replace(tmp, p)


def mint_full(gd):
    """全绿签发夹具铸造（test_report_lint.Base._mint 同款 argv+T8 授权修补）：
    EV 工件+EV 卡+FD finding+豁免行（cleanup 核销前置）→ sign 既有门全绿基线。"""
    art = os.path.join(gd, "evidence", EV_ID + ".raw")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8", newline="\n") as f:
        f.write(RAW_REQUEST)
    _repair_auth(gd)
    r = run(LEDGER, "add-evidence", "--goal-dir", gd,
            "--title=admin 面板匿名可读-实验组", "--source-type=capture",
            "--observed-at=2026-09-23T02:30:00Z", "--network-position=intranet",
            "--repro-command=curl -s http://admin-internal.shop.example/admin/orders",
            "--repro-kind=single", "--artifact=evidence/" + EV_ID + ".raw",
            "--raw-excerpt=HTTP/1.1 200 OK 订单列表脱敏样例（token 化后）",
            "--timestamp=2026-09-23T02:35:00Z")
    assert r.returncode == 0, r.stdout + r.stderr
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
    assert r.returncode == 0, r.stdout + r.stderr
    r = run(LEDGER, "approve", "--goal-dir", gd, "--command-hash=" + "b" * 64,
            "--decision=exempted", "--approver=客户",
            "--note=授权登记不可逆豁免 add-goal G-g1-0001",
            "--timestamp=2026-09-23T04:00:00Z")
    assert r.returncode == 0, r.stdout + r.stderr


class TestAuthorizationGate(unittest.TestCase):
    """签发四门①授权完整性（T8）：sha256 比对+窗口门+approvals verify-signoff。"""

    def _ready(self):
        """全绿签发基线（授权三件套齐+EV/FD/豁免齐）——反例的承载面。"""
        td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, td, True)
        gd = shutil.copytree(FIX, os.path.join(td, "G-g1"))
        mint_full(gd)
        return gd

    def test_deadbeef_sha_blocked(self):
        """专家反例③前半：auth_sha256=deadbeef（与 auth 文件实 sha 不符）→ sign 照发。"""
        gd = self._ready()
        _set_goals_cell(gd, "auth_sha256", DEAD)
        rc, rep = report_lint.sign_gate(gd, TS, write_credential=True)
        self.assertEqual(rc, 1, "红现状：全绿基线上换 deadbeef → sign rc=0（零授权校验）\n%s"
                         % rep)
        self.assertEqual(rep["gates"]["authorization"]["status"], "FAIL")
        self.assertIn("sha256", rep["gates"]["authorization"]["detail"])

    def test_expired_window_blocked(self):
        """专家反例③后半：授权窗口改 2020（已过期）→ 当下时刻 sign 照发 rc=0。"""
        gd = self._ready()
        _set_goals_cell(gd, "valid_until", "2020-12-31")
        rc, rep = report_lint.sign_gate(gd, TS, write_credential=True)
        self.assertEqual(rc, 1, "红现状：窗口 2020 过期 → sign rc=0（零窗口校验）\n%s" % rep)
        self.assertIn("过期", rep["gates"]["authorization"]["detail"])

    def test_zero_approvals_blocked_and_approved_passes_gate(self):
        """专家反例①：零 approved 行 sign 直通；批准在案后 authorization 门转 PASS。"""
        gd = self._ready()
        _strip_approved(gd)
        rc, rep = report_lint.sign_gate(gd, TS, write_credential=True)
        self.assertEqual(rc, 1, "红现状：零 approvals 校验 → sign rc=0\n%s" % rep)
        self.assertIn("approvals", rep["gates"]["authorization"]["detail"],
                      "零 approved 行=FAIL")
        # 追加 approved 行（真 CLI 通道）→ authorization 门细节消、全门可绿
        r = run(LEDGER, "approve", "--goal-dir", gd, "--command-hash=" + "c" * 64,
                "--decision=approved", "--approver=合规总监",
                "--note=T8 授权批准在案", "--timestamp=2026-09-23T02:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rc2, rep2 = report_lint.sign_gate(gd, TS, write_credential=False)
        self.assertEqual(rc2, 0, "三件套齐备的基线必须可绿（补批准后）\n%s" % rep2)
        self.assertEqual(rep2["gates"]["authorization"]["status"], "PASS")

    def test_lint_shares_gate(self):
        """lint 与 sign 同门：deadbeef 走 lint 入口同样拒收（不落凭证路径不豁免）。"""
        gd = self._ready()
        _set_goals_cell(gd, "auth_sha256", DEAD)
        r = run(REPORT, "lint", "--goal-dir", gd, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 1,
                         "红现状：lint 零授权校验 rc=0（deadbeef 直通）\n" + r.stdout)
        self.assertIn("authorization", r.stdout, "lint 报告须载 authorization 门")


if __name__ == "__main__":
    unittest.main()
