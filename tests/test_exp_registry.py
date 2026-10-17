# -*- coding: utf-8 -*-
"""实验登记处（exp registry）——预登记纪律与 directive-n5 回填（计划 R1）。

python3 -m unittest tests.test_exp_registry
律（docs/superpowers/plans/2026-10-14-exp-registry.md）：登记处=仓库根
experiments/<exp-id>.tsv（field\tvalue 行式 key-value，11 字段）；预登记先落 tsv
再开战；判决后回填 verdict；无登记=度量页不认。只读投影零写入、纯 stdlib、3.9 兼容。

directive-n5 机械验证结论（2026-10-14，真实数据 ~/.tanyin/battles 只读跑出）：
  候选子集逐战 recall 值与 HANDOFF:1358 全匹配，但池化 McNemar 得 b=3 c=0 p=0.25；
  受约束穷举（值匹配组合 3×1）与全空间穷举（6758 个 ≤5v≤5 子集）均无 b=8 c=17
  → verdict 按计划记「子集不可复原」（诚实收场）。
"""
import json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
REPO = os.path.dirname(CLI)
sys.path.insert(0, CLI)

from webui import metrics as met_mod  # noqa: E402

EXP_FIELDS = ("id", "question", "battles_control", "battles_treatment", "gt_gen",
              "decision_rule", "registered", "status", "verdict", "source", "note")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class RegistryBase(unittest.TestCase):
    def make_root(self, files):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        for name, text in files.items():
            write(os.path.join(td.name, "experiments", name), text)
        return td.name


class TestRegistryFormatV09d(RegistryBase):
    """R1 格式律：tsv 行式 field\tvalue 读回 dict / 缺字段降级 / 坏行与坏文件跳过。"""

    def test_roundtrip_full_fields(self):
        rows = "".join("%s\tv-%s\n" % (k, k) for k in EXP_FIELDS)
        root = self.make_root({"e1.tsv": rows})
        out = met_mod.experiments_view(root)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], dict((k, "v-" + k) for k in EXP_FIELDS))

    def test_missing_fields_degrade_to_empty(self):
        """缺字段 → 空串降级（不炸不缺键）。"""
        root = self.make_root({"e2.tsv": "id\te2\nquestion\tq?\n"})
        out = met_mod.experiments_view(root)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["id"], "e2")
        for k in EXP_FIELDS:
            self.assertIn(k, out[0])
        self.assertEqual(out[0]["note"], "")
        self.assertEqual(out[0]["verdict"], "")

    def test_bad_lines_skipped_only_tsv_parsed(self):
        """无制表符坏行跳过；非 .tsv 文件不认；无 id 的登记跳过（降级）。"""
        root = self.make_root({
            "e3.tsv": "id\te3\n坏行无制表符\nquestion\tq\n",
            "README.md": "# 律\n",
            "e4.txt": "id\te4\n",
            "e5.tsv": "question\t无 id 登记跳过\n"})
        out = met_mod.experiments_view(root)
        self.assertEqual([e["id"] for e in out], ["e3"])
        self.assertEqual(out[0]["question"], "q")

    def test_no_experiments_dir_empty_list(self):
        """无 experiments 目录 / 空目录 → 空表（度量页显示「无预登记实验」）。"""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.assertEqual(met_mod.experiments_view(td.name), [])
        self.assertEqual(met_mod.experiments_view(os.path.join(td.name, "none")), [])
        os.makedirs(os.path.join(td.name, "x", "experiments"))
        self.assertEqual(met_mod.experiments_view(os.path.join(td.name, "x")), [])

    def test_sorted_by_id_and_deterministic(self):
        root = self.make_root({
            "z-late.tsv": "id\tz-late\n",
            "a-first.tsv": "id\ta-first\n",
            "m-mid.tsv": "id\tm-mid\n"})
        out = met_mod.experiments_view(root)
        self.assertEqual([e["id"] for e in out], ["a-first", "m-mid", "z-late"])
        self.assertEqual(out, met_mod.experiments_view(root))


class TestBackfillDirectiveN5(RegistryBase):
    """R1 回填 directive-n5：登记文件在库、字段齐、子集清单与 HANDOFF 考据一致。"""

    @staticmethod
    def _entry():
        for e in met_mod.experiments_view(REPO):
            if e["id"] == "directive-n5":
                return e
        return None

    def test_registry_file_exists_and_complete(self):
        e = self._entry()
        self.assertIsNotNone(e, "experiments/directive-n5.tsv 未登记")
        for k in EXP_FIELDS:
            self.assertTrue(e[k], "directive-n5 字段空：%s" % k)

    def test_battles_match_handoff_inference(self):
        """子集清单=HANDOFF:1358 值匹配反推（对照 b29 b30 b35 b36 b37/处置 b28 b38 b39 b40 b42）。"""
        e = self._entry()
        self.assertIsNotNone(e)
        self.assertEqual(e["battles_control"].split(),
                         ["b29", "b30", "b35", "b36", "b37"])
        self.assertEqual(e["battles_treatment"].split(),
                         ["b28", "b38", "b39", "b40", "b42"])

    def test_verdict_honest_nonreproducible(self):
        """机械验证不复现 → verdict 记「子集不可复原」+note 说明（诚实收场）。"""
        e = self._entry()
        self.assertIsNotNone(e)
        self.assertIn("不可复原", e["verdict"])
        self.assertIn("b=3", e["note"])            # 现行数据机械复现值入账
        self.assertIn("HANDOFF", e["source"])      # 出处=值匹配考据

    def test_readme_law_exists(self):
        p = os.path.join(REPO, "experiments", "README.md")
        self.assertTrue(os.path.exists(p), "experiments/README.md 缺")
        with open(p, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("预登记", src)               # 先落 tsv 再开战
        self.assertIn("tsv", src)


class TestWiringV09d(unittest.TestCase):
    """R2 度量页接线：metrics_view/api/metrics.json 增 experiments 键、页面有节点。"""

    @staticmethod
    def _mini_home():
        """最小两臂夹具（1 对照+1 处置，各有 settle）——只够装配不炸即可。"""
        td = tempfile.TemporaryDirectory()
        home = td.name
        bl = os.path.join(home, "battles")
        write(os.path.join(home, "gt", "G-x1.json"),
              '{"planted": [{"id": "gt-1"}, {"id": "gt-2"}]}')
        write(os.path.join(bl, "battle-1", "directive.txt"), "")
        write(os.path.join(bl, "battle-1", "G-x1", "findings.tsv"), "id\n")
        write(os.path.join(bl, "battle-1", "settle-report.txt"),
              "verify-chain: PASS\nrecall=0.50 (1/2)\nMISSING\tgt-2\n")
        write(os.path.join(bl, "battle-2", "directive.txt"), "【指令】x")
        write(os.path.join(bl, "battle-2", "G-x1", "findings.tsv"), "id\n")
        write(os.path.join(bl, "battle-2", "settle-report.txt"),
              "verify-chain: PASS\nrecall=1.00 (2/2)\n")
        return td, bl

    def test_metrics_view_has_experiments_key(self):
        """metrics_view 输出增 experiments 键（=登记处默认根投影，列表）。"""
        td, bl = self._mini_home()
        self.addCleanup(td.cleanup)
        m = met_mod.metrics_view(bl)
        self.assertIn("experiments", m)
        self.assertIsInstance(m["experiments"], list)
        self.assertEqual(m["experiments"], met_mod.experiments_view())

    def test_default_root_is_repo(self):
        """默认根=cli/webui/metrics.py 上三级（登记处挂仓库根/experiments）。"""
        self.assertEqual(met_mod.default_repo_root(), os.path.realpath(REPO))
        self.assertEqual(met_mod.experiments_view(), met_mod.experiments_view(REPO))

    def test_experiments_view_is_readonly(self):
        """只读律钉死：读登记处前后，临时夹具与真实登记处目录树字节不变。"""
        td, _bl = self._mini_home()
        self.addCleanup(td.cleanup)
        root = td.name
        write(os.path.join(root, "experiments", "e.tsv"), "id\te\n")
        before = _tree_bytes(os.path.join(root, "experiments"))
        met_mod.experiments_view(root)
        self.assertEqual(_tree_bytes(os.path.join(root, "experiments")), before)
        repo_before = _tree_bytes(os.path.join(REPO, "experiments"))
        met_mod.experiments_view(REPO)
        met_mod.experiments_view()
        self.assertEqual(_tree_bytes(os.path.join(REPO, "experiments")), repo_before)

    def test_page_has_experiments_section(self):
        """metrics.html：「提前登记实验」小节节点+空登记文案（无登记显示）。"""
        p = os.path.join(CLI, "webui", "static", "metrics.html")
        with open(p, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('id="experiments"', src)
        # 文案随 v0.9d 收口批人话律词表：预登记→提前登记
        self.assertIn("无提前登记实验", src)
        self.assertIn("提前登记实验", src)


class ServerBaseV09d(unittest.TestCase):
    """v0.9c ServerBase 同款：真实 HTTP 服务器（临时端口）+TANYIN_HOME 夹具注入。"""

    def setUp(self):
        td, bl = TestWiringV09d._mini_home()
        self.td, self.bl = td, bl
        self.addCleanup(td.cleanup)
        self.home = td.name
        from webui import server as srv_mod
        from tests import webui_login
        self.srv = srv_mod.make_server("127.0.0.1", 0, self.home,
                                       tail=3, poll_s=0.05, keepalive_s=1.0,
                                       operator_key=webui_login.OP_KEY)
        self.port = self.srv.server_address[1]
        import threading
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop_server)
        self.sid = webui_login.login(self.port)   # B舰 P0 后：读面须会话
        self._old_home = os.environ.pop("TANYIN_HOME", None)
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
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        conn.request("GET", path, headers=webui_login.cookie(self.sid))
        return conn, conn.getresponse()


class TestServerExperimentsV09d(ServerBaseV09d):
    """R2 服务端：/api/metrics.json 带 experiments 键且 directive-n5 在册可见。"""

    def test_api_has_experiments_with_backfill(self):
        conn, resp = self._get("/api/metrics.json")
        self.assertEqual(resp.status, 200)
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertIn("experiments", data)
        self.assertIsInstance(data["experiments"], list)
        self.assertIn("directive-n5",
                      [e["id"] for e in data["experiments"]])   # 回填在册
        for k in ("battles", "stats", "mcnemar"):                # 旧键不丢（零破坏）
            self.assertIn(k, data)


def _tree_bytes(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


if __name__ == "__main__":
    unittest.main()
