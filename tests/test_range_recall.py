# -*- coding: utf-8 -*-
"""批次6 T16：授权靶场种 20+检出率 scorer（裁决 I；eval_authz_recall 匹配规则泛化复用）。

夹具级测试不依赖 docker（scorer 对夹具会话回归——CI 无 docker 降级语义面）；
compose 语法自检步 docker 缺=skipTest 并记录（裁决 I）。夹具 mint=diff-authz
卡片铸造法（make_diff_fixture 同款：add-evidence 后覆写卡片富化 expected.matchers）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "cli"))
import eval_range_recall  # noqa: E402  T16 红点：模块缺=ImportError 全红

FIX = os.path.join(HERE, "fixtures", "G-g1")
GT_PATH = os.path.join(HERE, "range", "ground-truth.json")
COMPOSE = os.path.join(HERE, "range", "docker-compose.yml")
TS = "2026-09-24T10:00:00Z"
SCORER = os.path.join(HERE, "eval_range_recall.py")

# 夹具 GT：3 命中（2 pre-auth+1 post-auth）+1 未命中 → recall=3/4
GT_FIX = [
    {"id": "fx-pre-1", "class": "sqli", "endpoint": "http://app.intranet:8000/a",
     "marker": "GTFIX-A", "post_auth": False, "authz_role": ""},
    {"id": "fx-pre-2", "class": "xss", "endpoint": "http://app.intranet:8000/b",
     "marker": "GTFIX-B", "post_auth": False, "authz_role": ""},
    {"id": "fx-post-1", "class": "idor", "endpoint": "http://app.intranet:8000/c",
     "marker": "GTFIX-C", "post_auth": True, "authz_role": "user"},
    {"id": "fx-miss-1", "class": "ssti", "endpoint": "http://app.intranet:8000/d",
     "marker": "GTFIX-D", "post_auth": False, "authz_role": ""},
]
GT_DISTRIBUTION = {"sqli": 2, "xss": 4, "cmdi": 2, "ssti": 2, "ssrf": 3, "deser": 3,
                   "cors": 2, "redir": 3, "traversal": 2, "idor": 4, "hauth": 3,
                   "role": 2, "weakpass": 1, "infoleak": 3, "lfi": 2, "rfi": 1,
                   "jwt": 2, "ratelimit": 2, "graphql": 2, "xxe": 1, "csrf": 2,
                   "userenum": 1, "upload": 1}


def run(*args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([sys.executable] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=e)


class TestGroundTruth(unittest.TestCase):
    def setUp(self):
        with open(GT_PATH, encoding="utf-8") as f:
            self.doc = json.load(f)               # 机读面={format_version,note,planted,host_aliases}
        self.gt = self.doc["planted"]

    def test_gt_shape_fifty(self):
        self.assertEqual(len(self.gt), 50)
        post = [g for g in self.gt if g["post_auth"]]
        self.assertGreaterEqual(len(post), 5)          # 认证后 ≥5（设计 §9.4；扩编后=10）
        self.assertEqual(len({g["marker"] for g in self.gt}), 50)   # marker 全局唯一
        self.assertEqual(len({g["id"] for g in self.gt}), 50)
        for g in self.gt:
            self.assertEqual(set(g.keys()),
                             {"id", "class", "endpoint", "marker", "post_auth", "authz_role"})
            if g["post_auth"]:
                self.assertTrue(g["authz_role"], "post_auth 条目 authz_role 非空")

    def test_gt_v3_contract_pins(self):
        """批次 9 评审收口（doc-consistency/automation）：format_version=3（v3=query
        剥离口径入册）+别名表含 svc-*:8000 容器形（防 raw_request 形资产键失配）。"""
        self.assertEqual(self.doc["format_version"], 3)
        for svc, al in self.doc["host_aliases"].items():
            self.assertIn(svc + ":8000", al,
                          "别名缺容器形 %s:8000（doc-consistency P2 端口残留陷阱）" % svc)

    def test_gt_distribution_fixed(self):
        """裁决 I 固定分布（批次 9 扩编 20→50）：八新类（lfi/rfi/jwt/ratelimit/
        graphql/xxe/csrf/userenum）+存量加密；post_auth=10。"""
        from collections import Counter
        c = Counter(g["class"] for g in self.gt)
        self.assertEqual(dict(c), GT_DISTRIBUTION)
        self.assertEqual(sum(1 for g in self.gt if g["post_auth"]), 10)


class Base(unittest.TestCase):
    """夹具会话=G-g1 复制+CLI 铸造（diff-authz 卡片铸造法）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gd = shutil.copytree(FIX, os.path.join(self.tmp, "G-g1"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _led(self, *args):
        r = run(os.path.join(ROOT, "cli", "tanyin-ledger"), args[0],
                "--goal-dir", self.gd, *args[1:])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout.splitlines()[0].split("\t")[1]

    def _card(self, ev, marker):
        """EV 卡覆写：expected.matchers word=marker（diff-authz 同款富化）。"""
        p = os.path.join(self.gd, "evidence", ev + ".md")
        text = ("---\nid: %s\ntitle: 靶场夹具证据\nsource_type: command\n"
                "observed_at: %s\nnetwork_position: intranet\npreconditions: []\n"
                "raw_request: |\n  GET /probe HTTP/1.1\n  Host: svc-fix\n"
                "expected:\n  matchers:\n    - {type: word, words: [\"%s\"]}\n"
                "cleanup: ''\npair_group: \nrole: \n---\n"
                "## 原始响应摘录（脱敏+定长）与判定依据\nmarker=%s\n"
                % (ev, TS, marker, marker))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def _mint(self, post_auth_chain=True):
        """3 命中+1 未命中夹具；post_auth_chain=False 时 post-auth finding 无 authz 链。"""
        ep = {"a": "http://app.intranet:8000/a", "b": "http://app.intranet:8000/b",
              "c": "http://app.intranet:8000/c"}
        self._led("add-scope", "--kind=account-grant", "--matcher=app.intranet",
                  "--account=admin", "--permitted-actions=read;probe",
                  "--timestamp=" + TS)
        self._led("add-scope", "--kind=include", "--matcher=app.intranet",
                  "--timestamp=" + TS)   # 批次 10 联查断言前置：资产须在 include 面
        ast = {k: self._led("add-asset", "--type=endpoint", "--value=" + v,
                            "--meta=range-fixture", "--timestamp=" + TS)
               for k, v in ep.items()}
        os.makedirs(os.path.join(self.gd, "art"), exist_ok=True)
        for k in ("a", "b", "c"):
            with open(os.path.join(self.gd, "art", "fx-%s.txt" % k), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write("marker=GTFIX-%s\n" % k.upper())

        def _ev(letter, marker):
            return self._led("add-evidence", "--title=夹具证据 " + letter.upper(),
                             "--source-type=command",
                             "--observed-at=" + TS, "--network-position=intranet",
                             "--repro-command=curl http://app.intranet:8000/" + letter,
                             "--repro-kind=single",
                             "--artifact=art/fx-%s.txt" % letter,
                             "--raw-excerpt=marker=" + marker,
                             "--timestamp=" + TS)

        ev_a = _ev("a", "GTFIX-A")
        self._card(ev_a, "GTFIX-A")
        ev_b = _ev("b", "GTFIX-B")
        self._card(ev_b, "GTFIX-B")
        ev_c = _ev("c", "GTFIX-C")
        self._card(ev_c, "GTFIX-C")
        for key, ev in (("a", ev_a), ("b", ev_b), ("c", ev_c)):
            self._led("append-timeline", "--actor=子代理", "--phase=P3",
                      "--event=probe:fx-" + key, "--revert-cmd=undo",
                      "--timestamp=" + TS)
        f1 = self._led("add-finding", "--intent-id=INT-g1-0002",
                       "--title=夹具命中 A", "--confidence=C2", "--impact=中",
                       "--exploitation-status=suspected", "--scope-check=in_scope",
                       "--description-brief=pre-auth", "--reproducible-steps=GET /a",
                       "--affected-asset-id=" + ast["a"], "--evidence-ids=" + ev_a,
                       "--timestamp=" + TS)
        f2 = self._led("add-finding", "--intent-id=INT-g1-0002",
                       "--title=夹具命中 B", "--confidence=C2", "--impact=中",
                       "--exploitation-status=suspected", "--scope-check=in_scope",
                       "--description-brief=pre-auth", "--reproducible-steps=GET /b",
                       "--affected-asset-id=" + ast["b"], "--evidence-ids=" + ev_b,
                       "--timestamp=" + TS)
        if post_auth_chain:
            cred = self._led("add-cred", "--kind=static-cred", "--role=user",
                             "--username-ref=u1", "--secret-ref={{vault:cred-2}}",
                             "--scope-asset=" + ast["c"],
                             "--permitted-actions=read", "--timestamp=" + TS)
            iid = self._led("add-intent", "--title=authz-diff app.intranet",
                            "--engine=web-blackbox", "--kind=authz-diff",
                            "--origin=entity", "--cred=" + cred,
                            "--detail=(app.intranet, user) 差分对",
                            "--actions=read", "--budget-share=1k;5;0.1",
                            "--timestamp=" + TS)
        else:
            cred, iid = "", "INT-g1-0002"      # 无 authz 链（负向夹具）
        args = ["add-finding", "--intent-id=" + iid, "--title=夹具命中 C",
                "--confidence=C2", "--impact=中", "--exploitation-status=suspected",
                "--scope-check=in_scope", "--description-brief=post-auth",
                "--reproducible-steps=GET /c", "--affected-asset-id=" + ast["c"],
                "--evidence-ids=" + ev_c, "--timestamp=" + TS]
        if cred:
            args.insert(1, "--auth-context=" + cred)
        f3 = self._led(*args)
        for ev in (ev_a, ev_b, ev_c):        # 精度门：夹具铸重放 VERIFIED 在案
            self._led("append-timeline", "--actor=CLI", "--phase=P4",
                      "--event=replay:%s:VERIFIED" % ev,
                      "--revert-cmd=none", "--timestamp=" + TS)
        return {"assets": ast, "findings": (f1, f2, f3), "evs": (ev_a, ev_b, ev_c)}


class TestScorer(Base):
    def _load(self):
        return eval_range_recall.load_session(self.gd)

    def test_scorer_perfect_fixture(self):
        self._mint()
        rows, cards = self._load()
        recall, missing = eval_range_recall.score(rows, cards, GT_FIX)
        self.assertAlmostEqual(recall, 3 / 4)
        self.assertEqual(missing, ["fx-miss-1"])       # MISSING 含未命中 id

    def test_scorer_ignores_query_form(self):
        """批次 9 三轮战教训（G-r4 归因：query 形罚 10 枚+CRED 链 4 枚）：GT 键含 query（参数名/值/编码）而
        诚实黑盒战士的探测参数不可预知（种子按路径前缀匹配行为）——键形 v3=
        host+path，query 整体剥离（RUNBOOK v3 口径；battle-2 作者读 GT 对齐掩盖）。
        路径段中的资源 id（/invoice/2 vs /invoice/88）为同型残留，本测试不覆盖
        （v4 候选：路径尾段数字化归一）。"""
        self._mint()
        rows, cards = self._load()
        gt_q = [dict(e) for e in GT_FIX]
        gt_q[0]["endpoint"] = "http://app.intranet:8000/a?page=..%2F..%2Fx"
        gt_q[1]["endpoint"] = "http://app.intranet:8000/b?tpl=%7B%7B7*7%7D%7D"
        gt_q[2]["endpoint"] = "http://app.intranet:8000/c?user_id=101"
        recall, missing = eval_range_recall.score(rows, cards, gt_q)
        self.assertAlmostEqual(recall, 3 / 4, "query 形差不得惩罚 host+path 命中")
        self.assertEqual(missing, ["fx-miss-1"])

    def test_host_aliases_positive_hit(self):
        """swe 专家 P1 钉（批次 9 评审）：语义别名正匹配回归——GT 条目端点写别名形
        （proxy.intranet）而会话资产=canonical 形（app.intranet）时，dict 形 GT 的
        host_aliases 必须把别名归一到 canonical 使命中成立（首战 0/20 正是该层故障，
        既往 12 测全 list 形 GT 从不触发该路径——退化也不红）。"""
        self._mint()
        rows, cards = self._load()
        gt_doc = {"host_aliases": {"app.intranet:8000": ["proxy.intranet:8000"]},
                  "planted": [dict(e) for e in GT_FIX]}
        gt_doc["planted"][0]["endpoint"] = "http://proxy.intranet:8000/a"
        recall, missing = eval_range_recall.score(rows, cards, gt_doc)
        self.assertAlmostEqual(recall, 3 / 4, msg="别名形 GT 条目须命中 canonical 资产")
        self.assertEqual(missing, ["fx-miss-1"])

    def test_precision_gate_requires_replay_verified(self):
        """批次 9 三轮战精度门（G-52）：命中前置=证据链有 replay VERIFIED 在案——
        幻觉/未验面零分；未翻案 not-reproduced 裁决拖累整 finding（CLI 缝⑪的
        评分侧纵深）。"""
        m = self._mint()
        # ① 撤掉 ev_b 的 VERIFIED 行（补 REJECTED 末值）→ b 面不计
        self._led("append-timeline", "--actor=CLI", "--phase=P4",
                  "--event=replay:%s:REJECTED" % m["evs"][1],
                  "--revert-cmd=none", "--timestamp=" + TS)
        rows, cards = self._load()
        recall, missing = eval_range_recall.score(rows, cards, GT_FIX)
        self.assertAlmostEqual(recall, 2 / 4)
        self.assertIn("fx-pre-2", missing)
        # ② ev_a 注 not-reproduced 探针裁决（无更晚 reproduced）→ a 面不计
        self._led("append-timeline", "--actor=子代理", "--phase=P4",
                  "--event=replay-probe %s verdict=not-reproduced" % m["evs"][0],
                  "--revert-cmd=none", "--timestamp=" + TS)
        rows, cards = self._load()
        recall, missing = eval_range_recall.score(rows, cards, GT_FIX)
        self.assertAlmostEqual(recall, 1 / 4)
        self.assertIn("fx-pre-1", missing)

    def test_post_auth_requires_authz_chain(self):
        """命中 marker 但无 authz 链的 post_auth 条目不计命中（负向）。"""
        self._mint(post_auth_chain=False)
        rows, cards = self._load()
        recall, missing = eval_range_recall.score(rows, cards, GT_FIX)
        self.assertAlmostEqual(recall, 2 / 4)
        self.assertIn("fx-post-1", missing)

    def test_score_empty_session_zero(self):
        rows, cards = self._load()
        recall, missing = eval_range_recall.score(rows, cards, GT_FIX)
        self.assertEqual(recall, 0.0)
        self.assertEqual(len(missing), 4)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.base = Base("setUp")
        self.base.setUp()

    def tearDown(self):
        self.base.doCleanups()

    def test_cli_exit_codes(self):
        self.base._mint()
        # baseline 超过实测（夹具会话对真实 GT recall=0）→ 1
        r = run(SCORER, "--session", self.base.gd, "--ground-truth", GT_PATH,
                "--baseline", "0.99")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        r = run(SCORER, "--session", self.base.gd, "--ground-truth", GT_PATH,
                "--baseline", "0.5")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        # baseline=0（recall>=baseline 即过）→ 0
        r = run(SCORER, "--session", self.base.gd, "--ground-truth", GT_PATH,
                "--baseline", "0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("recall=", r.stdout)

    def test_cli_docker_missing_no_session_exit_2(self):
        """docker 缺且无 --session → exit 2（裁决 I 降级；PATH 剥离确定性模拟）。"""
        r = run(SCORER, "--ground-truth", GT_PATH, env={"PATH": "/nonexistent"})
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_cli_session_missing_exit_2(self):
        r = run(SCORER, "--session", os.path.join(self.base.tmp, "nope"),
                "--ground-truth", GT_PATH)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)


class TestRangeArtifacts(unittest.TestCase):
    def test_compose_config(self):
        """compose 语法自检（docker compose config；docker 缺=skip 并记录，裁决 I）。"""
        if shutil.which("docker") is None:
            self.skipTest("docker 缺（ENV-skip 降级，裁决 I）")
        r = subprocess.run(["docker", "compose", "-f", COMPOSE, "config", "-q"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_gt_seed_marker_consistency(self):
        """每 GT marker 在 seed 源码恰出现一次（种 20 可复铸一致性）。"""
        with open(GT_PATH, encoding="utf-8") as f:
            gt = json.load(f)["planted"]
        blob = []
        for dirpath, _dirs, files in os.walk(os.path.join(HERE, "range", "seed")):
            for fn in sorted(files):
                if fn.endswith(".py"):
                    with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                        blob.append(fh.read())
        src = "\n".join(blob)
        for g in gt:
            self.assertEqual(src.count(g["marker"]), 1, g["id"])

    def test_compose_lists_eight_services(self):
        with open(COMPOSE, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text.count("build: ./seed/"), 8)   # 8 漏洞服务容器
        self.assertIn("attack-noop", text)                   # 攻击侧 noop
        # M-3 评审收尾：range 网 internal:true（漏洞服务零出网）；internal 网下
        # published ports 被 compose 丢弃（实测 config rc=0 而宿主连接拒）——死映射
        # 不得声明，探针改经 attack-noop 双网跳板（range+egress 出网例外）。
        self.assertIn("internal: true", text)
        self.assertNotIn("127.0.0.1:", text)
        self.assertRegex(text, r"attack-noop:[\s\S]*?egress")


if __name__ == "__main__":
    unittest.main()
