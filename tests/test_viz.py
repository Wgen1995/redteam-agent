# -*- coding: utf-8 -*-
"""批次4 T11：tanyin-viz 投影——数据岛/身份矩阵视图/findings 流/零回写/确定性。

计划 3 例（数据岛自包含/零回写/两次渲染字节一致）+ 追加件增补例
（docs/design/2026-09-24-finding-stream-priority.md fb72cd5：findings 实时流投影——
最新 N 条时间/资产/类型/severity/状态，high/critical 置顶标记，确定性输出）。"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
VIZ = os.path.join(ROOT, "cli", "tanyin-viz")
LEDGER = os.path.join(ROOT, "cli", "tanyin-ledger")
FIXD = os.path.join(HERE, "fixtures", "diff-authz")
TS = "2026-09-24T11:00:00Z"   # 晚于夹具 findings（2026-09-24T10:00:00Z）


def fingerprint(gd):
    out = []
    for dirpath, _d, files in os.walk(gd):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            out.append(os.path.relpath(p, gd) + ":"
                       + hashlib.sha256(open(p, "rb").read()).hexdigest()[:12])
    return sorted(out)


def render(gd, out):
    return subprocess.run([sys.executable, VIZ, "render", "--goal-dir", gd, "--out", out],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def data_only(gd):
    return subprocess.run([sys.executable, VIZ, "render", "--goal-dir", gd, "--data-only"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestViz(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIXD, os.path.join(self.tmp, "diff-authz"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_selfcontained_with_authz_view(self):
        out = os.path.join(self.tmp, "session.html")
        r = render(self.gd, out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = open(out, encoding="utf-8").read()
        self.assertIn('id="tanyin-data"', html)
        self.assertNotIn("http://", html.replace("http://www.w3.org", ""),
                         "零外部引用（W3C 命名空间除外）")
        island = html.split('id="tanyin-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        data = json.loads(island)
        for k in ("stats", "phases", "graph", "rightpanel", "authz_matrix", "findings_stream"):
            self.assertIn(k, data)
        self.assertTrue(data["authz_matrix"]["endpoints"], "身份矩阵视图非空（role×endpoint 投影）")
        self.assertIn("coverage", data["authz_matrix"])

    def test_zero_writeback(self):
        before = fingerprint(self.gd)
        render(self.gd, os.path.join(self.tmp, "session.html"))
        self.assertEqual(fingerprint(self.gd), before, "projector 零回写")

    def test_deterministic(self):
        digests = []
        for i in range(2):
            out = os.path.join(self.tmp, "s%d.html" % i)
            render(self.gd, out)
            digests.append(hashlib.sha256(open(out, "rb").read()).hexdigest())
        self.assertEqual(digests[0], digests[1], "两次渲染字节一致（确定性）")


class TestFindingStream(unittest.TestCase):
    """追加件（fb72cd5）：findings 实时流——最新 N 条+high/critical 置顶。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIXD, os.path.join(self.tmp, "diff-authz"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_stream_latest_n_pinned_top(self):
        # 经 CLI 追加一条 中 severity finding（created=TS 晚于夹具三条 高）→
        # R-T4-2（批次5 T4 夹具重铸）：diff-authz 经 set-replay-state --timestamp 铸
        # VERIFIED 重放事件行后，findings.tsv 多一条合法追加行（FD-diff-authz-0001
        # created=10:30，VERIFIED→verified 联动）——流投影按行不按 id 去重，随之 3→4 条。
        # 置顶段=[FD-diff-authz-0001(10:30), FD-diff-authz-0001(10:00), FD-g1-0001(空=最旧)]，
        # 非置顶段=[新 中(11:00)]
        r = subprocess.run([sys.executable, LEDGER, "add-finding", "--goal-dir", self.gd,
                            "--intent-id=INT-diff-authz-0001", "--title=流投影低危样例",
                            "--confidence=C3", "--impact=中", "--exploitation-status=suspected",
                            "--scope-check=in_scope", "--description-brief=低危流条目",
                            "--reproducible-steps=curl -s https://app.intranet/x",
                            "--affected-asset-id=AST-diff-authz-0001",
                            "--evidence-ids=EV-diff-authz-0001", "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = data_only(self.gd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fs = json.loads(r.stdout)["findings_stream"]
        self.assertEqual(len(fs["items"]), 4)
        for it in fs["items"]:
            for k in ("time", "asset", "type", "severity", "status", "pinned"):
                self.assertIn(k, it)
        self.assertEqual([it["pinned"] for it in fs["items"]], [True, True, True, False],
                         "high/critical 置顶段在前、其余在后")
        self.assertEqual(fs["items"][0]["id"], "FD-diff-authz-0001", "置顶段内按新近排序")
        self.assertEqual(fs["items"][3]["severity"], "中")
        self.assertTrue(fs["pinned_high"] >= 2, "置顶计数")
        # 确定性：双跑 --data-only 字节一致
        r2 = data_only(self.gd)
        self.assertEqual(r.stdout, r2.stdout)


if __name__ == "__main__":
    unittest.main()
