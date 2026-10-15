# -*- coding: utf-8 -*-
"""v0.9c 度量页——双臂召回曲线/McNemar/逐战明细（计划 Task M1-M2）。

python3 -m unittest tests.test_v09c_metrics
律（docs/design/tanyin-target-form.md §1/§3 + 计划共同律）：只读投影零写入、
纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。

数据真相（scripts/battle.py cmd_settle → tests/eval_range_recall.py 实勘）：
  <TANYIN_HOME>/battles/battle-N/settle-report.txt —— 首行 verify-chain（半/全角
  冒号两代），正文 recall=H/T 行 + MISSING\t<gt-id> 行；臂标记=directive.txt 字节数
  （>0=处置臂预置指令 / =0=对照臂 / 缺文件=早期战未知臂）；GT 位=<home>/gt/<gen>.json
  （battle 目录 G-* 子目录即 gen；缺 GT → per_item={} 配对降级不炸）。
"""
import importlib.util, json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from webui import metrics as met_mod  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "rerun", os.path.join(HERE, "..", "scripts", "rerun.py"))
rerun = importlib.util.module_from_spec(_spec)   # 口径基准（v0.6 H3 同款精确 McNemar）
_spec.loader.exec_module(rerun)

GT8 = ["gt-%02d" % i for i in range(1, 9)]       # 8 枚 GT 项（合成分母）
CONTROL, TREAT = "对照", "处置"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def report(chain_sep=":", chain="PASS", recall=None, missing=()):
    head = ("verify-chain%s %s\n" % (chain_sep, chain)) if chain else ""
    body = ("recall=%.2f (%d/%d)\n" % (recall[0] / recall[1], recall[0], recall[1])
            if recall else "findings.tsv 不存在——战未毕或未开铸\n")
    return head + body + "".join("MISSING\t%s\n" % m for m in missing)


def build_home(td):
    """合成两臂战例场：battle-1 对照 / 2-3 处置 / 4 未知臂（无 directive）/
    5 未结算（无 recall 行）/ 6 空目录 / 7 对照但 gen 无 GT 文件（配对降级）/
    op-1 非 battle-N 目录（须忽略）。GT=8 项放 <td>/gt/G-x9.json。"""
    bl = os.path.join(td, "battles")
    write(os.path.join(td, "gt", "G-x9.json"), json.dumps(
        {"planted": [{"id": i} for i in GT8], "host_aliases": {}}))
    write(os.path.join(bl, "battle-1", "directive.txt"), "")            # 对照：0B
    write(os.path.join(bl, "battle-1", "G-x9", "findings.tsv"), "id\n")
    write(os.path.join(bl, "battle-1", "settle-report.txt"),
          report(recall=(6, 8), missing=("gt-03", "gt-07")))
    write(os.path.join(bl, "battle-2", "directive.txt"), "【b28 预置指令】1. 慢速退避")
    write(os.path.join(bl, "battle-2", "G-x9", "findings.tsv"), "id\n")
    write(os.path.join(bl, "battle-2", "settle-report.txt"),
          report(chain_sep="：", recall=(4, 8),                          # 全角冒号（格式多代）
                 missing=("gt-02", "gt-03", "gt-05", "gt-08")))
    write(os.path.join(bl, "battle-3", "directive.txt"), "【指令】2. 铸卡纪律")
    write(os.path.join(bl, "battle-3", "G-x9", "findings.tsv"), "id\n")
    write(os.path.join(bl, "battle-3", "settle-report.txt"),
          report(chain="FAIL", recall=(5, 8), missing=("gt-01", "gt-04", "gt-08")))
    write(os.path.join(bl, "battle-4", "G-x9", "findings.tsv"), "id\n")  # 无 directive=未知臂
    write(os.path.join(bl, "battle-4", "settle-report.txt"),
          report(chain="", recall=(7, 8), missing=("gt-06",)))
    write(os.path.join(bl, "battle-5", "settle-report.txt"), report())    # 未结算 → 跳过
    os.makedirs(os.path.join(bl, "battle-6"))                            # 空目录 → 跳过
    write(os.path.join(bl, "battle-7", "directive.txt"), "")             # 对照但 GT 缺 → 降级
    write(os.path.join(bl, "battle-7", "G-absent", "findings.tsv"), "id\n")
    write(os.path.join(bl, "battle-7", "settle-report.txt"),
          report(recall=(3, 8), missing=("gt-01", "gt-03", "gt-05", "gt-06", "gt-07")))
    write(os.path.join(bl, "op-1", "settle-report.txt"),
          report(recall=(8, 8)))                                         # 非 battle-N → 忽略
    return bl


def tree_bytes(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.home = self.td.name
        self.bl = build_home(self.home)


class TestParseSettleV09c(unittest.TestCase):
    """settle-report 解析：recall 行（rerun._RECALL 同款）+MISSING 行+chain 容错。"""

    def test_parse_full_and_variants(self):
        r = met_mod.parse_settle("verify-chain: PASS\n\nrecall=0.70 (39/56)\n"
                                 "track_beacon=39\nMISSING\trole-01\nMISSING\thauth-01\n")
        self.assertEqual((r["hits"], r["total"]), (39, 56))
        self.assertAlmostEqual(r["recall"], 39 / 56, places=4)
        self.assertEqual(r["missing"], ["role-01", "hauth-01"])
        self.assertEqual(r["chain"], "PASS")
        r2 = met_mod.parse_settle("verify-chain：FAIL\nrecall=0.41 (23/56)\n")
        self.assertEqual(r2["chain"], "FAIL")          # 全角冒号（格式多代容错）
        self.assertIsNone(met_mod.parse_settle("findings.tsv 不存在——战未毕或未开铸\n"))

    def test_parse_chain_absent(self):
        r = met_mod.parse_settle("recall=0.50 (4/8)\nMISSING\tgt-02\n")
        self.assertEqual(r["chain"], "")               # 无 verify-chain 行 → 空串
        self.assertEqual(r["missing"], ["gt-02"])


class TestBattlesMetricsV09c(Base):
    """M1 battles_metrics：逐战 {id,arm,recall,hits,total,per_item}+两臂统计+池化 McNemar。"""

    def test_shape_ordering_and_skips(self):
        m = met_mod.battles_metrics(self.bl)
        self.assertEqual([b["id"] for b in m["battles"]],
                         ["battle-1", "battle-2", "battle-3", "battle-4", "battle-7"])
        for b in m["battles"]:                          # 逐战六键齐（计划契约）
            for k in ("id", "arm", "recall", "hits", "total", "per_item"):
                self.assertIn(k, b)
        self.assertEqual(m["battles"][0]["hits"], 6)
        self.assertEqual(m["battles"][0]["total"], 8)

    def test_arm_markers_multigen(self):
        """臂标记=directive 字节数；缺文件=未知臂（None，早期战降级）。"""
        by = {b["id"]: b["arm"] for b in met_mod.battles_metrics(self.bl)["battles"]}
        self.assertEqual(by["battle-1"], CONTROL)      # 0B=对照
        self.assertEqual(by["battle-2"], TREAT)        # >0B=处置
        self.assertEqual(by["battle-3"], TREAT)
        self.assertIsNone(by["battle-4"])              # 无 directive=未知臂
        self.assertEqual(by["battle-7"], CONTROL)

    def test_per_item_full_with_gt(self):
        m = met_mod.battles_metrics(self.bl)
        b1 = m["battles"][0]
        self.assertEqual(b1["per_item"],
                         {"gt-01": True, "gt-02": True, "gt-03": False, "gt-04": True,
                          "gt-05": True, "gt-06": True, "gt-07": False, "gt-08": True})
        self.assertEqual(b1["missing"], ["gt-03", "gt-07"])

    def test_per_item_degrades_without_gt(self):
        """GT 文件缺 → per_item={}（配对降级不炸）；missing 清单仍在。"""
        m = met_mod.battles_metrics(self.bl)
        b7 = [b for b in m["battles"] if b["id"] == "battle-7"][0]
        self.assertEqual(b7["per_item"], {})
        self.assertEqual(len(b7["missing"]), 5)

    def test_stats_two_arms(self):
        st = met_mod.battles_metrics(self.bl)["stats"]
        self.assertEqual(st[CONTROL], {"n": 2, "mean": 0.5625, "min": 0.375, "max": 0.75})
        self.assertEqual(st[TREAT], {"n": 2, "mean": 0.5625, "min": 0.5, "max": 0.625})

    def test_mcnemar_pooled(self):
        """池化配对（臂内任一战命中即命中）：b=1(gt-08) c=2(gt-03,07) → n=3 p=1.0。"""
        mc = met_mod.battles_metrics(self.bl)["mcnemar"]
        self.assertEqual(mc["b"], 1)
        self.assertEqual(mc["c"], 2)
        self.assertEqual(mc["n"], 3)
        self.assertEqual(mc["p"], 1.0)
        self.assertEqual(mc["shared"], 8)
        self.assertIn("无显著差异", mc["verdict"])

    def test_mcnemar_none_when_one_arm(self):
        home2 = os.path.join(self.td.name, "h2")
        bl2 = os.path.join(home2, "battles")
        write(os.path.join(home2, "gt", "G-x9.json"), json.dumps(
            {"planted": [{"id": i} for i in GT8]}))
        write(os.path.join(bl2, "battle-9", "directive.txt"), "")
        write(os.path.join(bl2, "battle-9", "G-x9", "findings.tsv"), "id\n")
        write(os.path.join(bl2, "battle-9", "settle-report.txt"),
              report(recall=(8, 8)))
        m = met_mod.battles_metrics(bl2)
        self.assertIsNone(m["mcnemar"])                # 单臂 → 无配对（诚实降级）
        self.assertEqual(m["stats"][CONTROL]["n"], 1)

    def test_empty_battles_dir(self):
        empty = os.path.join(self.td.name, "none", "battles")
        os.makedirs(empty)
        m = met_mod.battles_metrics(empty)
        self.assertEqual(m["battles"], [])
        self.assertEqual(m["stats"], {})
        self.assertIsNone(m["mcnemar"])

    def test_readonly_law(self):
        """只读律：装配前后全目录树字节不变钉死。"""
        before = tree_bytes(self.home)
        met_mod.battles_metrics(self.bl)
        met_mod.metrics_view(self.bl)
        self.assertEqual(tree_bytes(self.home), before)

    def test_deterministic_and_json(self):
        a, b = met_mod.battles_metrics(self.bl), met_mod.battles_metrics(self.bl)
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_default_path_env(self):
        """默认路径=TANYIN_HOME（或 ~/.tanyin）/battles——battle.py BASE 同源。"""
        old = os.environ.pop("TANYIN_HOME", None)
        os.environ["TANYIN_HOME"] = self.home
        try:
            self.assertEqual(met_mod.battles_metrics(),
                             met_mod.battles_metrics(self.bl))
        finally:
            os.environ.pop("TANYIN_HOME", None)
            if old is not None:
                os.environ["TANYIN_HOME"] = old


def _pair(items_a, items_b):
    return met_mod.mcnemar_exact(items_a, items_b)


def _mk(ids_hit_a, ids_hit_b, ids=GT8 + ["gt-%02d" % i for i in range(9, 41)]):
    a = {i: (i in ids_hit_a) for i in ids}
    b = {i: (i in ids_hit_b) for i in ids}
    return a, b


class TestMcnemarV09c(unittest.TestCase):
    """M1 mcnemar_exact：共有 GT 项配对；exact 二项与 rerun.py 口径逐点对齐。"""

    def test_known_sample_b8_c17(self):
        """已知样本（N=5 双臂活体判决）：b=8 c=17 → p≈0.108。"""
        only_a = GT8                                                        # 8 枚仅 A 命中
        only_b = ["gt-%02d" % i for i in range(9, 26)]                         # 17 枚仅 B 命中
        both = ["gt-%02d" % i for i in range(26, 36)]                          # 10 枚双命中（协同对）
        a, b = _mk(only_a + both, only_b + both)
        r = _pair(a, b)
        self.assertEqual((r["b"], r["c"], r["n"]), (8, 17, 25))
        self.assertAlmostEqual(r["p"], 0.108, delta=0.0005)
        self.assertEqual(r["p"], 0.107752)   # = rerun.mcnemar_exact(8,17) 同值

    def test_aligns_with_rerun_semantics(self):
        """p 与 scripts/rerun.py mcnemar_exact(b,c) 逐点相等（settle 口径单源）。"""
        for bb, cc in ((8, 17), (0, 0), (8, 0), (3, 4), (1, 9), (5, 5), (2, 12)):
            ids = ["k%02d" % i for i in range(bb + cc + 4)]
            hit_a = set(ids[:bb]) | set(ids[bb + cc:])
            hit_b = set(ids[bb:bb + cc]) | set(ids[bb + cc:])
            r = _pair({i: i in hit_a for i in ids}, {i: i in hit_b for i in ids})
            self.assertEqual((r["b"], r["c"]), (bb, cc), (bb, cc))
            self.assertEqual(r["p"], rerun.mcnemar_exact(bb, cc), (bb, cc))

    def test_pairs_only_on_shared(self):
        """只对两臂共有 GT 项集合配对：独有项不入 b/c。"""
        ids = ["s1", "s2", "s3"]
        a = {"s1": True, "s2": False, "s3": True, "a-only": True}
        b = {"s1": False, "s2": True, "s3": True, "b-only": False}
        r = _pair(a, b)
        self.assertEqual((r["b"], r["c"], r["n"]), (1, 1, 2))
        self.assertEqual(r["p"], 1.0)

    def test_edges(self):
        self.assertEqual(_pair({}, {}), {"b": 0, "c": 0, "n": 0, "p": 1.0})
        same = {i: True for i in GT8}
        self.assertEqual(_pair(same, same)["p"], 1.0)  # 全协同对 → 无差异
        self.assertEqual(_pair(same, {})["n"], 0)      # 无共有项 → n=0 不炸


class ServerBaseV09c(unittest.TestCase):
    """v0.9b ServerBase 同款：真实 HTTP 服务器（临时端口）+TANYIN_HOME 夹具注入。"""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.home = self.td.name
        self.bl = build_home(self.home)
        from webui import server as srv_mod
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.home,
                                       tail=3, poll_s=0.05, keepalive_s=1.0)
        self.port = self.srv.server_address[1]
        import threading
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop_server)
        self._old_home = os.environ.pop("TANYIN_HOME", None)   # 度量装配走 env 注入
        os.environ["TANYIN_HOME"] = self.home
        self.addCleanup(self._restore_home)

    def _stop_server(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _restore_home(self):
        os.environ.pop("TANYIN_HOME", None)
        if self._old_home is not None:
            os.environ["TANYIN_HOME"] = self._old_home

    def _get(self, path, timeout=5):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path)
        return conn, conn.getresponse()


class TestServerRoutesV09c(ServerBaseV09c):
    """M2 路由：/metrics 页 + /api/metrics.json（_PAGE_API 单源表挂载）。"""

    def test_metrics_page(self):
        conn, resp = self._get("/metrics")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("text/html"))
        self.assertIn('id="chart"', resp.read().decode("utf-8"))
        conn.close()

    def test_api_metrics_json(self):
        conn, resp = self._get("/api/metrics.json")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        for k in ("battles", "stats", "mcnemar"):
            self.assertIn(k, data)
        self.assertEqual(len(data["battles"]), 5)      # 未结算/空目录/非 battle-N 已跳过
        self.assertIn(CONTROL, data["stats"])
        self.assertIn(TREAT, data["stats"])
        for k in ("b", "c", "n", "p", "shared", "verdict"):
            self.assertIn(k, data["mcnemar"])

    def test_api_hits_are_readonly(self):
        """投影律（服务端）：页+API 各打一轮，夹具目录树字节不变。"""
        before = tree_bytes(self.home)
        for p in ("/metrics", "/api/metrics.json"):
            conn, resp = self._get(p)
            self.assertEqual(resp.status, 200, p)
            resp.read()
            conn.close()
        self.assertEqual(tree_bytes(self.home), before)

    def test_404_unknown_still(self):
        conn, resp = self._get("/nope")
        self.assertEqual(resp.status, 404)
        conn.close()


STATIC_V09C = os.path.join(CLI, "webui", "static")


class TestIndexNavV09c(unittest.TestCase):
    """首页导航加「度量」一链（v0.9c 六页 IA 收口）。"""

    def test_nav_has_metrics(self):
        with open(os.path.join(STATIC_V09C, "index.html"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn('href="/metrics"', src)


class TestPageV09c(unittest.TestCase):
    """metrics.html 语言律：零框架零 CDN、单页 JS<2000 行、关键节点在。"""

    @staticmethod
    def _src():
        with open(os.path.join(STATIC_V09C, "metrics.html"), encoding="utf-8") as f:
            return f.read()

    def test_containers_fetch_and_arms(self):
        src = self._src()
        self.assertIn("/api/metrics.json", src)
        for m in ('id="chart"', 'id="legend"', 'id="stats"', 'id="table"',
                  "createElementNS", CONTROL, TREAT):
            self.assertIn(m, src, "metrics.html 缺 " + m)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertNotIn("<script src=", src)
        self.assertNotIn("https://", src)
        self.assertNotIn("http://", src.replace("http://www.w3.org", ""))

    def test_js_under_2000_lines(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 2000)


if __name__ == "__main__":
    unittest.main()
