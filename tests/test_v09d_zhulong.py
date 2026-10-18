# -*- coding: utf-8 -*-
"""v0.9d Ship Z：ZhuLong findings 互通（zhulong-export）TDD 钉。

契约面=ZhuLong /api/imports（apps/server/src/services/import-service.ts 实勘）：
  POST {base}/api/imports，鉴权=Cookie zl_sess（POST /api/auth/login {username,password}
  →Set-Cookie）；请求体 ImportCreateBodySchema＝{engineId, sourceDir, projectId,
  objectId?, envId?}；导入源=tanyin@1 mapper（mapper-tanyin.ts）消费的平铺五族
  （findings.tsv 19 列/E-index.tsv 16 列/timeline.tsv 8 列/edges.tsv 7 列/EV-*.md/
  FD-*.md）+battle-report.md（manifest required pattern）。
本测试钉四事：①dry-run 默认生成 JSON 导入包且字段对齐契约；②导出内容过 vault
脱敏（tokenize_output 同值漂移钉）；③dry-run 零网络；④--push 才真发（登录→cookie→
POST，_stub 服务器验请求形）。Python 3.9 纯 stdlib。
"""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import vault  # noqa: E402
from ledger import zhulong_export  # noqa: E402

CLI = os.path.join(ROOT, "cli", "tanyin-ledger")
FIX = os.path.join(ROOT, "tests", "fixtures", "G-g1")
TAB = chr(9)
SECRET = "s3cret-token-9f2a"
TS = "2026-10-15T00:00:00Z"


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def make_goal(td, with_vault=False, with_cards=True):
    """G-g1 骨架＋三行 findings/两行 E-index/gate-exit+replay timeline/attack 边。"""
    gd = os.path.join(td, "G-g1")
    shutil.copytree(FIX, gd)
    rows_fd = [
        TAB.join(["FD-g1-0001", "INT-g1-0002", "svc-shop /items SQLi 报错回显 " + SECRET,
                  "C1", "高", "verified", "", "AST-g1-0002+CWE-89", "CWE-89", "in_scope",
                  "匿名 GET 直取即触发", "1.GET /items 2.观察回显", "AST-g1-0002",
                  "EV-g1-0001;EV-g1-0002", "", "findings-cards/FD-g1-0001.md",
                  "active", "2", TS]),
        TAB.join(["FD-g1-0002", "INT-g1-0002", "svc-shop /search 反射 XSS",
                  "C2", "中", "suspected", "CRED-g1-0001", "AST-g1-0002+CWE-79", "CWE-79",
                  "in_scope", "q 参数回显未编码", "1.GET /search 2.观察回显", "AST-g1-0002",
                  "EV-g1-0003", "", "findings-cards/FD-g1-0002.md",
                  "active", "2", TS]),
        TAB.join(["FD-g1-0003", "INT-g1-0003", "/logout 开放重定向（合并弃用）",
                  "C3", "低", "verified", "", "AST-g1-0003+CWE-601", "CWE-601", "in_scope",
                  "302 跳转", "1.GET /logout", "AST-g1-0003", "EV-g1-0004", "",
                  "findings-cards/FD-g1-0003.md", "superseded", "2", TS]),
    ]
    _w(os.path.join(gd, "findings.tsv"), "".join(r + "\n" for r in rows_fd))
    rows_ev = [
        TAB.join(["EV-g1-0001", "/items 响应捕获", "capture", TS, "intranet",
                  "GET http://svc-shop:8000/items", "single", "a" * 64, "a" * 64,
                  "evidence/raw1.raw", "evidence/EV-g1-0001.md", "FD-g1-0001", "",
                  "<html>err " + SECRET + "</html>", "2", TS]),
        TAB.join(["EV-g1-0002", "/items 二次捕获", "capture", TS, "intranet",
                  "GET http://svc-shop:8000/items?again=1", "single", "b" * 64, "b" * 64,
                  "evidence/raw2.raw", "evidence/EV-g1-0002.md", "FD-g1-0001", "PG-7",
                  "<html>again</html>", "2", TS]),
    ]
    _w(os.path.join(gd, "E-index.tsv"), "".join(r + "\n" for r in rows_ev))
    _w(os.path.join(gd, "edges.tsv"),
       TAB.join(["E-g1-0001", "attack", "AST-g1-0001", "AST-g1-0002", "P3", "2", TS]) + "\n")
    tl = [
        TAB.join([TS, "总控", "P0", "add-goal G-g1-0001", "irreversible", "0" * 64, "1" * 64, "2"]),
        TAB.join([TS, "总控", "P0", "gate-exit:P0 asserts=3 result=PASS", "", "1" * 64, "2" * 64, "2"]),
        TAB.join([TS, "总控", "P3", "gate-exit:P3 asserts=1 result=PASS", "", "2" * 64, "3" * 64, "2"]),
        TAB.join([TS, "CLI", "P4", "replay:EV-g1-0001:VERIFIED note=reproduced " + SECRET, "",
                  "3" * 64, "4" * 64, "2"]),
    ]
    _w(os.path.join(gd, "timeline.tsv"), "".join(r + "\n" for r in tl))
    if with_cards:
        _w(os.path.join(gd, "evidence", "EV-g1-0001.md"),
           "---\nid: EV-g1-0001\ntitle: /items 响应捕获\nnetwork_position: intranet\n"
           "preconditions: [可解析内网域名]\nraw_request: |\n  GET /items HTTP/1.1\n"
           "  Authorization: Bearer " + SECRET + "\nexpected: {matchers: [{type: word, "
           "words: [\"GTSQLI-01\"]}]}\npair_group: \n---\n## 原始响应摘录\n<html>err</html>\n")
        _w(os.path.join(gd, "evidence", "EV-g1-0002.md"),
           "---\nid: EV-g1-0002\ntitle: 二次捕获\nnetwork_position: intranet\n"
           "raw_request: |\n  GET /items?again=1 HTTP/1.1\nexpected: word\n---\n摘录\n")
        _w(os.path.join(gd, "findings-cards", "FD-g1-0001.md"),
           "---\nid: FD-g1-0001\ndedup_key: AST-g1-0002+CWE-89\nscope_check: in_scope\n"
           "exploitation_status: verified\nconfidence: C1\nimpact: 高\n---\n"
           "## 漏洞叙述\n/items 拼接 SQL " + SECRET + "\n## 复现步骤\n引用 EV 卡\n"
           "## 修复建议叙述\n参数化查询\n")
        _w(os.path.join(gd, "findings-cards", "FD-g1-0002.md"),
           "---\nid: FD-g1-0002\nconfidence: C2\nimpact: 中\n---\n"
           "## 漏洞叙述\n/search 回显未编码\n## 复现步骤\n引用 EV 卡\n"
           "## 修复建议叙述\n输出编码\n")
        _w(os.path.join(gd, "findings-cards", "FD-g1-0003.md"),
           "---\nid: FD-g1-0003\nconfidence: C3\nimpact: 低\n---\n"
           "## 漏洞叙述\n302 跳转（已合并弃用）\n## 复现步骤\nGET /logout\n"
           "## 修复建议叙述\n白名单跳转域\n")
    if with_vault:
        key = "k" * 64
        os.makedirs(os.path.join(gd, "vault"), exist_ok=True)
        with open(os.path.join(gd, "vault", ".key"), "w", encoding="utf-8") as f:
            f.write(key + "\n")
        with open(os.path.join(gd, "vault", "cred-1.enc"), "w", encoding="utf-8") as f:
            f.write(vault.enc_payload(key, "admin" + chr(10) + SECRET))
        with open(os.path.join(gd, "vault", "manifest.tsv"), "w", encoding="utf-8") as f:
            f.write(TAB.join(["1", "cred-1.enc", "dead", "etm-sha256", "2"]) + "\n")
    return gd


def call(gd, *args):
    import io
    from contextlib import redirect_stdout, redirect_stderr
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = zhulong_export.HANDLERS["zhulong-export"](gd, list(args))
    return code, out.getvalue(), err.getvalue()


def load_guard():
    """tanyin-guard 无 .py 后缀——SourceFileLoader 装载（有 __main__ 守卫，导入安全）。"""
    loader = importlib.machinery.SourceFileLoader(
        "tanyin_guard_ref", os.path.join(ROOT, "cli", "tanyin-guard"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _read(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestDryRunPackage(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = make_goal(self.td.name)

    def test_dry_run_generates_contract_json_and_flat_files(self):
        code, out, err = call(self.gd, "--project-id=7", "--timestamp=" + TS)
        self.assertEqual(code, 0, err)
        out_dir = os.path.join(self.gd, "zhulong-export")
        names = sorted(os.listdir(out_dir))
        for req in ("findings.tsv", "E-index.tsv", "timeline.tsv", "edges.tsv",
                    "battle-report.md", "EV-g1-0001.md", "EV-g1-0002.md",
                    "FD-g1-0001.md", "zhulong-import.json"):
            self.assertIn(req, names, "导入包缺 " + req)
        # 平铺律：无子目录（mapper 按 basename 消费）
        for n in names:
            self.assertFalse(os.path.isdir(os.path.join(out_dir, n)), "包内不得有子目录: " + n)
        pkg = _load_json(os.path.join(out_dir, "zhulong-import.json"))
        self.assertEqual(pkg["mode"], "dry-run")
        # 契约字段对齐 ImportCreateBodySchema：五键全在，类型对齐
        body = pkg["import_request"]["body"]
        self.assertEqual(set(body), {"engineId", "sourceDir", "projectId", "objectId", "envId"})
        self.assertEqual(body["engineId"], "tanyin")
        self.assertEqual(body["projectId"], 7)
        self.assertIsInstance(body["projectId"], int)
        self.assertIsNone(body["objectId"])
        self.assertIsNone(body["envId"])
        self.assertEqual(body["sourceDir"], os.path.abspath(out_dir))
        self.assertTrue(os.path.isdir(body["sourceDir"]))
        # files 数组与盘上一致（sha256+字节）
        pkg_names = {f["name"] for f in pkg["files"]}
        self.assertEqual(pkg_names, set(names) - {"zhulong-import.json"})
        for f in pkg["files"]:
            data = open(os.path.join(out_dir, f["name"]), "rb").read()
            self.assertEqual(f["bytes"], len(data), f["name"] + " bytes 不符")
            self.assertEqual(f["content"], data.decode("utf-8"), f["name"] + " content 不符")
        # 五族 TSV 逐字节=源账本（本例无 vault→零替换）
        for t in ("findings.tsv", "E-index.tsv", "timeline.tsv", "edges.tsv"):
            src = open(os.path.join(self.gd, t), "rb").read()
            self.assertEqual(open(os.path.join(out_dir, t), "rb").read(), src, t + " 非逐字节拷贝")
        # battle-report 含 goal 与计数（manifest required pattern 命中）
        rep = _read(os.path.join(out_dir, "battle-report.md"))
        self.assertIn("G-g1-0001", rep)
        self.assertIn("active=2", rep)
        self.assertIn("superseded=1", rep)

    def test_object_env_ids_flow_into_body(self):
        code, _, err = call(self.gd, "--project-id=9", "--object-id=3", "--env-id=5",
                            "--timestamp=" + TS)
        self.assertEqual(code, 0, err)
        pkg = _load_json(os.path.join(self.gd, "zhulong-export", "zhulong-import.json"))
        self.assertEqual(pkg["import_request"]["body"]["objectId"], 3)
        self.assertEqual(pkg["import_request"]["body"]["envId"], 5)

    def test_missing_project_id_is_usage_error(self):
        code, _, err = call(self.gd, "--timestamp=" + TS)
        self.assertEqual(code, 2)
        self.assertIn("project-id", err)

    def test_out_pointing_at_goal_dir_rejected(self):
        code, _, err = call(self.gd, "--project-id=7", "--out=" + self.gd)
        self.assertEqual(code, 2)
        self.assertIn("账本", err)

    def test_positional_rejected(self):
        code, _, err = call(self.gd, "extra", "--project-id=7")
        self.assertEqual(code, 2)

    def test_missing_findings_table_fails_closed(self):
        os.remove(os.path.join(self.gd, "findings.tsv"))
        code, _, err = call(self.gd, "--project-id=7")
        self.assertEqual(code, 1)
        self.assertIn("findings.tsv", err)

    def test_missing_cards_degrade_with_warning(self):
        os.remove(os.path.join(self.gd, "evidence", "EV-g1-0001.md"))
        code, _, err = call(self.gd, "--project-id=7", "--timestamp=" + TS)
        self.assertEqual(code, 0, err)
        self.assertIn("EV-g1-0001", err)   # 缺卡 WARNING 侧记（mapper TSV 兜底同语义）
        pkg = _load_json(os.path.join(self.gd, "zhulong-export", "zhulong-import.json"))
        self.assertEqual(pkg["counts"]["ev_cards"], 1)
        self.assertEqual(pkg["counts"]["cards_missing"], 1)


class TestRedaction(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.gd = make_goal(self.td.name, with_vault=True)

    def test_vault_secret_never_leaves_goal_dir(self):
        code, _, err = call(self.gd, "--project-id=7", "--timestamp=" + TS)
        self.assertEqual(code, 0, err)
        out_dir = os.path.join(self.gd, "zhulong-export")
        for n in os.listdir(out_dir):
            data = _read(os.path.join(out_dir, n))
            self.assertNotIn(SECRET, data, n + " 泄漏 vault 真值")
        fd = _read(os.path.join(out_dir, "findings.tsv"))
        self.assertIn("{{vault:cred-1}}", fd, "findings 标题未换占位符")
        ev = _read(os.path.join(out_dir, "EV-g1-0001.md"))
        self.assertIn("{{vault:cred-1}}", ev, "EV 卡 raw_request 未换占位符")
        tl = _read(os.path.join(out_dir, "timeline.tsv"))
        self.assertIn("{{vault:cred-1}}", tl, "timeline 事件未换占位符")
        pkg = _load_json(os.path.join(out_dir, "zhulong-import.json"))
        self.assertNotIn(SECRET, json.dumps(pkg))
        self.assertEqual(pkg["redaction"]["vault_secrets"], 1)
        self.assertGreater(pkg["redaction"]["token_counts"].get("cred-1", 0), 0)
        self.assertIn("{{vault:cred-1}}", pkg["files"][0]["content"] if
                      pkg["files"][0]["name"].endswith(".tsv") else "{{vault:cred-1}}")


class TestTokenizeDrift(unittest.TestCase):
    """与 tanyin-guard.tokenize_output 同值漂移钉（长值优先语义单源）。"""

    def test_same_output_as_guard(self):
        guard = load_guard()
        secrets = [("2", "short"), ("1", "short-but-much-longer-secret")]
        corpus = ["", "nothing", "a short day", "xshort-but-much-longer-secrety short",
                  SECRET + " short " + chr(9) + "short"]
        for text in corpus:
            self.assertEqual(zhulong_export._tokenize(text, secrets),
                             guard.tokenize_output(text, secrets), repr(text))


class TestZeroNetwork(unittest.TestCase):
    def test_dry_run_never_touches_network(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        gd = make_goal(td.name)
        calls = []
        orig = zhulong_export._urlreq.urlopen

        def bomb(*a, **kw):
            calls.append(a)
            raise AssertionError("dry-run 不得发起网络请求")
        zhulong_export._urlreq.urlopen = bomb
        try:
            code, _, err = call(gd, "--project-id=7", "--timestamp=" + TS,
                                "--url=http://127.0.0.1:1")
            self.assertEqual(code, 0, err)
        finally:
            zhulong_export._urlreq.urlopen = orig
        self.assertEqual(calls, [])


class _Stub(BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        _Stub.seen.append((self.path, dict(self.headers), body))
        if self.path == "/api/auth/login":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "zl_sess=stub-token-42; Path=/; HttpOnly")
            self.end_headers()
            self.wfile.write(b'{"id":1,"username":"wgen","role":"admin"}')
            return
        if self.path == "/api/imports":
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"taskId": 11, "stageCount": 2, "artifactCount": 7,
                                         "findingCount": 2, "failures": []}).encode())
            return
        self.send_response(404)
        self.end_headers()


class TestPush(unittest.TestCase):
    def setUp(self):
        _Stub.seen = []
        self.srv = HTTPServer(("127.0.0.1", 0), _Stub)
        self.base = "http://127.0.0.1:%d" % self.srv.socket.getsockname()[1]
        self.th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.th.start()
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(self.srv.server_close)
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.gd = make_goal(td.name)

    def _env(self, user="wgen", pw="pw12345678"):
        saved = {k: os.environ.get(k) for k in
                 ("TANYIN_ZHULONG_USER", "TANYIN_ZHULONG_PASS", "TANYIN_ZHULONG_URL")}
        for k, v in (("TANYIN_ZHULONG_USER", user), ("TANYIN_ZHULONG_PASS", pw)):
            os.environ[k] = v
        os.environ.pop("TANYIN_ZHULONG_URL", None)

        def restore():
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.addCleanup(restore)

    def test_push_logins_then_imports(self):
        self._env()
        code, out, err = call(self.gd, "--push", "--project-id=7",
                              "--url=" + self.base, "--timestamp=" + TS)
        self.assertEqual(code, 0, err + out)
        paths = [s[0] for s in _Stub.seen]
        self.assertEqual(paths, ["/api/auth/login", "/api/imports"])
        login_body = _Stub.seen[0][2]
        self.assertEqual(set(login_body), {"username", "password"})
        self.assertEqual(login_body["username"], "wgen")
        imp_headers, imp_body = _Stub.seen[1][1], _Stub.seen[1][2]
        self.assertIn("zl_sess=stub-token-42", imp_headers.get("Cookie", ""))
        self.assertEqual(set(imp_body), {"engineId", "sourceDir", "projectId",
                                         "objectId", "envId"})
        self.assertEqual(imp_body["engineId"], "tanyin")
        self.assertEqual(imp_body["projectId"], 7)
        self.assertTrue(os.path.isdir(imp_body["sourceDir"]))
        self.assertIn("OK push taskId=11", out)
        self.assertIn("findingCount=2", out)
        pkg = _load_json(os.path.join(self.gd, "zhulong-export", "zhulong-import.json"))
        self.assertEqual(pkg["mode"], "push")

    def test_push_without_credentials_is_env_error(self):
        saved = {k: os.environ.get(k) for k in ("TANYIN_ZHULONG_USER", "TANYIN_ZHULONG_PASS")}
        for k in ("TANYIN_ZHULONG_USER", "TANYIN_ZHULONG_PASS"):
            os.environ.pop(k, None)
        self.addCleanup(lambda: [os.environ.__setitem__(k, v) if v is not None
                                 else os.environ.pop(k, None) for k, v in saved.items()])
        code, _, err = call(self.gd, "--push", "--project-id=7", "--url=" + self.base)
        self.assertEqual(code, 2)
        self.assertIn("TANYIN_ZHULONG_USER", err)


class TestEntryWiring(unittest.TestCase):
    def test_tanyin_ledger_dispatches_zhulong_export(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        gd = make_goal(td.name)
        out = os.path.join(gd, "zhulong-export")
        r = subprocess.run([sys.executable, CLI, "zhulong-export", "--goal-dir", gd,
                            "--project-id=7", "--timestamp=" + TS],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(out, "zhulong-import.json")))
        # 命令面 48→49(Ship Z)→50(W2·01P0-2 intent-lease)→53(功能13补件二 retest 三命令)
        # →55(fafa34c 规划者I-3接线: planner-loop-start/trigger 两CLI入口)：
        # 入口挂载面=registry.all_commands()∪zhulong_export.HANDLERS
        from ledger import registry
        face = registry.all_commands() | set(zhulong_export.HANDLERS)
        self.assertEqual(len(face), 55)
        self.assertIn("zhulong-export", face)


if __name__ == "__main__":
    unittest.main()
