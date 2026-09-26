# -*- coding: utf-8 -*-
"""批次6 T13：FD 九段渲染器+时间链断言（FD 规格 b0006f2 §一/§二 兑现）。

夹具=G-g1 复制+CLI 铸造（add-evidence 前置工件落盘锚双指纹→覆盖 EV 卡 raw_request
〔R-T5 批次4 预铸卡先例〕→add-finding）；raw_request 取无 body GET 形（受限 YAML 子集
块标量丢空行的解析实况——正文体请求走工件原件，见 HANDOFF R-T13-2）。时间戳全字面量。"""
import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import report_agg, report_render, cards  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
REPORT = os.path.join(ROOT, "cli", "tanyin-report")
TS = "2026-09-24T09:00:00Z"
EV_ID, FD_ID = "EV-g1-0002", "FD-g1-0002"
# 无 body GET 形（受限 YAML 块标量可无损承载；burp 规则④对无 body 请求不适用）
RAW_REQUEST = "GET /admin/orders HTTP/1.1\nHost: admin-internal.shop.example\nAccept: */*"


def run(*args):
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


class TestRender(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _mint(self):
        """CLI 铸 EV+FD：工件先落盘锚双指纹→add-evidence→覆盖卡→add-finding。"""
        gd = self.gd
        art = os.path.join(gd, "evidence", EV_ID + ".raw")
        os.makedirs(os.path.dirname(art), exist_ok=True)
        with open(art, "w", encoding="utf-8", newline="\n") as f:
            f.write(RAW_REQUEST)                      # 字节=卡值（双指纹一致锚）
        r = run(LEDGER, "add-evidence", "--goal-dir", gd,
                "--title=admin 面板匿名可读-实验组", "--source-type=capture",
                "--observed-at=2026-09-23T02:30:00Z", "--network-position=intranet",
                "--repro-command=curl -s http://admin-internal.shop.example/admin/orders",
                "--repro-kind=single", "--artifact=evidence/" + EV_ID + ".raw",
                "--raw-excerpt=HTTP/1.1 200 OK 订单列表脱敏样例（token 化后）",
                "--timestamp=2026-09-23T02:35:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        card = os.path.join(gd, "evidence", EV_ID + ".md")
        with open(card, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\nid: %s\ntitle: admin 面板匿名可读-实验组\nsource_type: capture\n"
                    % EV_ID
                    + "observed_at: 2026-09-23T02:30:00Z\nnetwork_position: intranet\n"
                    + "preconditions:\n  - 可解析 admin-internal.shop.example（DNS 内网视角）\n"
                    + "raw_request: |\n  GET /admin/orders HTTP/1.1\n"
                    + "  Host: admin-internal.shop.example\n  Accept: */*\n"
                    + "expected: {}\ncleanup: ''\npair_group: \nrole: \n---\n"
                    + "## 原始响应摘录（脱敏+定长）与判定依据\n"
                    + "HTTP/1.1 200 OK（脱敏样例：未登录可读订单列表，token 化后原文）\n")
        r = run(LEDGER, "add-finding", "--goal-dir", gd,
                "--intent-id=INT-g1-0002", "--title=admin 面板匿名可读（复核样本）",
                "--confidence=C1", "--impact=高", "--exploitation-status=verified",
                "--scope-check=in_scope", "--description-brief=未登录可读订单列表（渲染夹具）",
                "--reproducible-steps=匿名 GET /admin/orders;响应 200 含订单列表",
                "--affected-asset-id=AST-g1-0002", "--evidence-ids=" + EV_ID,
                "--timestamp=2026-09-23T03:30:00Z")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return FD_ID

    def _any_fd(self, gd):
        rows = report_agg.aggregate(gd, TS)["findings"]
        self.assertTrue(rows, "夹具无 active finding")
        return rows[0]["id"]

    def _ev_raw_request(self, gd):
        with open(os.path.join(gd, "E-index.tsv"), encoding="utf-8") as f:
            s_rows = [ln.split("\t") for ln in f.read().splitlines() if ln]
        cols = TABLES["E-index.tsv"]
        row = next(r for r in s_rows if r[0] == EV_ID)
        return cards.parse_ev_card(os.path.join(gd, row[cols.index("card_path")]))["raw_request"]

    SEGS = ["位置", "涉及资产与接口", "漏洞描述", "等级", "漏洞原理",
            "POC/EXP", "危害", "修复建议", "复现与验证状态"]

    def test_nine_segments_in_order(self):
        fd = self._mint()
        rc, md = report_render.render_fd(self.gd, fd)
        self.assertEqual(rc, 0, md)
        pos = [md.find("## " + s) for s in self.SEGS]
        self.assertTrue(all(p >= 0 for p in pos) and pos == sorted(pos),
                        "九段齐且有序: %r" % pos)

    def test_raw_request_byte_identical(self):
        self._mint()
        raw_ev = self._ev_raw_request(self.gd)         # EV 卡 POC 原文
        rc, md = report_render.render_fd(self.gd, FD_ID)
        self.assertEqual(rc, 0, md)
        self.assertIn(raw_ev, md)                      # 转抄零编辑

    def test_time_chain_ok_on_fixture(self):
        self._mint()
        ok, why = report_render.check_time_chain(self.gd)
        self.assertTrue(ok, why)
        ok2, why2 = report_render.check_time_chain(self.gd, TS)
        self.assertTrue(ok2, why2)                     # issued_at 晚于 added_at

    def test_time_chain_violation(self):
        self._mint()
        p = os.path.join(self.gd, "E-index.tsv")       # 夹具篡改：captured 晚于 added
        with open(p, encoding="utf-8") as f:
            rows = [ln.split("\t") for ln in f.read().splitlines() if ln]
        for r in rows:
            if r[0] == EV_ID:
                r[TABLES["E-index.tsv"].index("observed_at")] = "2026-09-23T04:30:00Z"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write("\t".join(r) + "\n")
        ok, why = report_render.check_time_chain(self.gd)
        self.assertFalse(ok)
        self.assertIn(EV_ID, why)

    def test_unverified_disclosed(self):
        self._mint()
        r = run(LEDGER, "set-replay-state", "--goal-dir", self.gd,
                "--id=" + FD_ID, "--state=REJECTED",
                "--timestamp=2026-09-23T05:00:00Z")   # CLI 铸造未过重放门
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rc, md = report_render.render_fd(self.gd, FD_ID)
        self.assertEqual(rc, 0, md)
        self.assertIn("未通过独立重放门", md)          # 披露行强制在
        self.assertNotIn("verified：是", md)

    def test_missing_source_rc1_with_gap_list(self):
        rc, msg = report_render.render_fd(self.gd, "FD-g1-0001")   # 历史行无证据/资产
        self.assertEqual(rc, 1)
        self.assertIn("缺段", msg)

    def test_vocab_miss_render_fail(self):
        self._mint()
        p = os.path.join(self.gd, "matrix.tsv")        # 夹具篡改：锚行类型不在词表
        with open(p, encoding="utf-8") as f:
            rows = [ln.split("\t") for ln in f.read().splitlines() if ln]
        for r in rows:
            if r[1] == "authz.diff":
                r[1] = "not.in.vocab"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write("\t".join(r) + "\n")
        rc, msg = report_render.render_fd(self.gd, FD_ID)
        self.assertEqual(rc, 1)
        self.assertIn("词表", msg)

    def test_cli_render_out_deterministic(self):
        self._mint()
        out1 = os.path.join(self.tmp, "d1.md")
        out2 = os.path.join(self.tmp, "d2.md")
        for out in (out1, out2):
            r = run(REPORT, "render", "--goal-dir", self.gd, "--fd=" + FD_ID,
                    "--out=" + out, "--timestamp=" + TS)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out1, "rb") as f1, open(out2, "rb") as f2:
            self.assertEqual(f1.read(), f2.read())
        with open(out1, encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("## 复现与验证状态", txt)

    def test_cli_render_all(self):
        self._mint()
        outdir = os.path.join(self.gd, "report", "draft")
        r = run(REPORT, "render", "--goal-dir", self.gd, "--all",
                "--out=" + outdir, "--timestamp=" + TS)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(outdir, FD_ID + ".md")))


if __name__ == "__main__":
    unittest.main()