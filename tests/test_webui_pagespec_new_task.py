# -*- coding: utf-8 -*-
"""T5·P4 新建任务（授权信息表单）——页钉测（界面线施工计划 2026-10-18 T5）。

python3 -m unittest tests.test_webui_pagespec_new_task
律：只读投影零写入、纯 stdlib、3.9 兼容、前端零框架零 CDN、单页 JS<2000 行。
设计权威 docs/design/ui-spec-complete-v1.md §P4（两列表单：左表单+右实时摘要卡
+sha256 即时显示+预估说明）；文案宪法#41（八问→新建任务；界面人话律）。
提交走既有 POST /api/battle/new（授权八问缺一=422 字段级拒因回显——四态齐备：
空/字段错[行内红]/提交中[按钮态]/服务端拒[顶部横幅]）。

三层钉：
  ①投影层  api_v2_tasks.new_task_meta_view——模板下拉（battle-kit BRIEF 模板
           既有件只读解析）+枚举+提交契约+八问清单（页面完备性指示器单源）；
  ②挂载层  GET /api/v2/new-task-meta.json 过会话门（_V2MountHandler 钉法同
           tests/test_webui_pagespec_tasks.py）；
  ③页面层  static/pages/new-task.html 结构钉——八问完备性实时指示器（八项哪项
           已齐/缺啥，齐了才亮「创建」）+授权书拖拽区（PDF/PNG+浏览器实算
           sha256）+范围逐行+预算三段+模板下拉+四态。
"""
import json
import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from webui import api_v2_tasks as api       # noqa: E402
from webui import server as srv_mod         # noqa: E402

PAGE_PATH = os.path.join(CLI, "webui", "static", "pages", "new-task.html")
REPO = os.path.join(CLI, "..")
KIT = os.path.join(REPO, "tests", "range", "battle-kit")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_kit(kit):
    """battle-kit 夹具：两模板——mission 形（八问结构行）+纯 prose 形。"""
    _write(os.path.join(kit, "BRIEF-template.md"),
           "# G-r4 三轮战简报\n\n## 任务\n目标：对 8 服务靶面穷尽 HTTP 探测。\n"
           "范围：include=*.range.local 与 172.28.0.0/24；exclude=*.out-of-scope.local\n"
           "预算：2M;50000;40\n")
    _write(os.path.join(kit, "BRIEF-forensic.md"),
           "# 仅取证模板\n\n只观察不利用。\n")
    _write(os.path.join(kit, "README.md"), "# kit 说明（非模板）\n目标：说明文件。\n")
    _write(os.path.join(kit, "boot-template.py"), "# 非模板\n")
    return kit


class MetaBase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.kit = build_kit(os.path.join(self.td.name, "kit"))


# ═══════════════════════════════ ① 投影层 ═══════════════════════════════

class TestNewTaskMeta(MetaBase):
    """模板下拉（battle-kit BRIEF 既有件）+枚举+提交契约+八问清单单源。"""

    def meta(self, **kw):
        kw.setdefault("kit_dir", self.kit)
        return api.new_task_meta_view(**kw)

    def test_templates_from_kit_md_only(self):
        """kit *.md 入下拉（py/readme 形不入——模板=BRIEF md 件）。"""
        d = self.meta()
        ids = [t["id"] for t in d["templates"]]
        self.assertIn("BRIEF-template", ids)
        self.assertIn("BRIEF-forensic", ids)
        self.assertNotIn("README", ids)
        self.assertNotIn("boot-template", ids)

    def test_template_mission_form_parse(self):
        """mission 形结构行提取：目标/范围 include 行/预算三段（缺=诚实空）。"""
        d = self.meta()
        t = {x["id"]: x for x in d["templates"]}["BRIEF-template"]
        self.assertEqual(t["objective"], "对 8 服务靶面穷尽 HTTP 探测。")
        self.assertEqual(t["scope_lines"], ["*.range.local", "172.28.0.0/24"])
        self.assertEqual(t["budget"], "2M;50000;40")
        f = {x["id"]: x for x in d["templates"]}["BRIEF-forensic"]
        self.assertEqual(f["objective"], "")
        self.assertEqual(f["scope_lines"], [])
        self.assertEqual(f["budget"], "")

    def test_enums_and_submit_contract(self):
        """枚举+提交契约单源（/api/battle/new 真实域——server._auth_eight_questions
        同表：model_tier strong|weak、guard_tier T1|T2|T3、legal_ack 真布尔）。"""
        d = self.meta()
        self.assertEqual(d["enums"]["model_tier"], ["strong", "weak"])
        self.assertEqual(d["enums"]["guard_tier"], ["T1", "T2", "T3"])
        self.assertEqual(d["enums"]["cred_source"],
                         ["客户提供", "自备（自行注册）", "盲测（无凭据探测）"])
        self.assertEqual(d["submit"]["endpoint"], "/api/battle/new")
        self.assertEqual(d["submit"]["method"], "POST")
        for k in ("name", "budget", "scope", "auth", "cred_source",
                  "emergency_contact", "model_tier", "guard_tier", "legal_ack"):
            self.assertIn(k, d["submit"]["requires"])

    def test_eight_question_list_single_source(self):
        """八问清单（页面指示器单源）：编号/键/标签与 server 校验域对齐。"""
        d = self.meta()
        self.assertEqual(len(d["eight"]), 8)
        keys = [q["key"] for q in d["eight"]]
        self.assertEqual(keys, ["auth_doc", "window", "legal", "scope",
                                "cred_source", "budget", "tier", "contact"])
        labels = "".join(q["label"] for q in d["eight"])
        for want in ("授权书", "窗口期", "法律确认", "范围", "凭据", "预算", "强度", "联系人"):
            self.assertIn(want, labels)

    def test_kit_dir_missing_tolerated(self):
        d = self.meta(kit_dir=os.path.join(self.td.name, "none"))
        self.assertEqual(d["templates"], [])
        self.assertEqual(len(d["eight"]), 8)      # 八问清单与 kit 无关恒在

    def test_readonly_deterministic_json(self):
        a = self.meta()
        b = self.meta()
        self.assertEqual(a, b)
        self.assertIsInstance(json.dumps(a, ensure_ascii=False), str)

    def test_route_and_dispatch(self):
        st, p = api.new_task_meta_route({}, kit_dir=self.kit)
        self.assertEqual(st, 200)
        self.assertTrue(p["templates"])
        st2, p2 = api.dispatch("/api/v2/new-task-meta.json", {}, kit_dir=self.kit)
        self.assertEqual(st2, 200)
        self.assertEqual(p2, p)
        self.assertIsNone(api.dispatch("/api/v2/nope", {}))


# ═══════════════════════════════ ② 挂载层 ═══════════════════════════════

class _V2MountHandler(srv_mod.Handler):
    """include 挂法钉（同 tasks 页钉法）：/api/v2/* 过会话门后分发 ROUTES。"""

    def do_GET(self):
        import urllib.parse
        u = urllib.parse.urlparse(self.path)
        if u.path.startswith("/api/v2/"):
            if not self._session_ok():
                return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            res = api.dispatch(u.path, q, self.server.ledger_dir,
                               kit_dir=getattr(self.server, "kit_dir", None))
            if res is not None:
                status, payload = res
                return self._send(status, "application/json",
                                  json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return super().do_GET()


class TestV2Mount(MetaBase):
    """/api/v2/new-task-meta.json 会话门+分发（动态口；禁碰 8900）。"""

    def setUp(self):
        super().setUp()
        from tests import webui_login
        self.srv = srv_mod.WebServer(
            ("127.0.0.1", 0), _V2MountHandler,
            ledger_dir=os.path.join(self.td.name, "ledger"),
            operator_key=webui_login.OP_KEY)
        self.srv.kit_dir = self.kit                    # 挂法钉：server 属性注入
        self.port = self.srv.server_address[1]
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(self._stop)
        self.sid = webui_login.login(self.port)

    def _stop(self):
        self.srv.stopping = True
        self.srv.shutdown()
        self.srv.server_close()

    def _get(self, path, cookie=True):
        import http.client
        from tests import webui_login
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        hdrs = webui_login.cookie(self.sid) if cookie else {}
        conn.request("GET", path, headers=hdrs)
        return conn, conn.getresponse()

    def test_401_without_session(self):
        conn, resp = self._get("/api/v2/new-task-meta.json", cookie=False)
        self.assertEqual(resp.status, 401)
        conn.close()

    def test_meta_over_http(self):
        conn, resp = self._get("/api/v2/new-task-meta.json")
        self.assertEqual(resp.status, 200)
        p = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(p["submit"]["endpoint"], "/api/battle/new")
        self.assertEqual(len(p["eight"]), 8)
        conn.close()


# ═══════════════════════════════ ③ 页面层 ═══════════════════════════════

ZONE_MARKS = (
    # 两列布局：左表单 / 右实时摘要卡
    'id="col-form"', 'id="col-summary"',
    # 基本信息组：名称/目标说明/模板下拉
    'id="f-name"', 'id="f-note"', 'id="f-template"',
    # 组「授权」：①拖拽区（PDF/PNG+sha256 即时显示）②窗口期 ③法律确认
    'id="drop-zone"', 'id="f-auth-file"', 'id="auth-sha"', 'id="auth-meta"',
    'id="f-signer"', 'id="f-valid-from"', 'id="f-valid-until"',
    'id="f-legal"',
    # 组「范围」：④白名单逐行 ⑤凭据来源
    'id="f-scope"', 'id="scope-tags"', 'id="f-cred"',
    # 组「资源」：⑥预算三段 ⑦强度档
    'id="f-budget-token"', 'id="f-budget-req"', 'id="f-budget-hours"',
    'id="f-model-tier"', 'id="f-guard-tier"',
    # ⑧联系人
    'id="f-contact"',
    # 八问完备性实时指示器（齐了才亮「创建」）
    'id="eight-list"', 'id="btn-create"', "crypto.subtle",
    # 四态：空（初态）/字段错（行内红）/提交中/服务端拒（顶部横幅）
    'id="srv-banner"', 'id="create-ok"',
    # 提交走既有 /api/battle/new
    "'/api/battle/new'",
    # 元信息单源消费
    "'/api/v2/new-task-meta.json'",
    # sha256 计算态（浏览器实算）
    "计算中",
)
FETCH_MARKS = ("'/api/v2/new-task-meta.json",)


class TestPageStructure(unittest.TestCase):
    def _src(self):
        with open(PAGE_PATH, encoding="utf-8") as f:
            return f.read()

    def test_zones_and_states_present(self):
        src = self._src()
        for m in ZONE_MARKS:
            self.assertIn(m, src, "缺 " + m)
        for m in FETCH_MARKS:
            self.assertIn(m, src, "须拉取 " + m)

    def test_create_gated_by_eight_complete(self):
        """八问齐备才亮「创建」——指示器逐项点灯+按钮 disabled 联动。"""
        src = self._src()
        self.assertIn("checkEight", src)
        self.assertIn("allEightDone", src)
        self.assertIn("disabled = !ready", src)

    def test_drag_pdf_png_only(self):
        src = self._src()
        self.assertIn('accept=".pdf,.png"', src)
        self.assertIn("application/pdf", src)
        self.assertIn("image/png", src)
        self.assertIn("dragover", src)
        self.assertIn("drop", src)

    def test_submit_body_shape(self):
        """提交体形钉：auth{filename,sha256,content_b64,signer,valid_from,
        valid_until}+scope 数组+legal_ack 真布尔——server._auth_eight_questions 域。"""
        src = self._src()
        for k in ("filename", "sha256", "content_b64", "signer",
                  "valid_from", "valid_until"):
            self.assertIn(k + ":", src)
        self.assertIn("legal_ack: legal", src)
        self.assertIn("X-Requested-With", src)

    def test_nav_self_registration_guarded(self):
        src = self._src()
        self.assertIn("nav.push", src)
        self.assertIn("id: 'new-task'", src)
        self.assertIn("label: '新建任务'", src)
        self.assertIn("typeof nav.push", src)

    def test_zero_framework_zero_cdn(self):
        src = self._src()
        self.assertEqual(src.count("<script src="), 1, "只许共享壳一外链")
        self.assertIn('<script src="/static/app.js"></script>', src)
        self.assertNotIn("https://", src)

    def test_page_over_500_lines_js_under_1500(self):
        src = self._src()
        blocks = src.split("<script>")[1:]
        self.assertGreaterEqual(len(blocks), 1)
        nlines = sum(len(b.split("</script>")[0].splitlines()) for b in blocks)
        self.assertLess(nlines, 1500)
        self.assertGreaterEqual(len(src.splitlines()), 500, "P4 全量页量纲")

    def test_js_hygiene_strict_loop_vars(self):
        import re as _re
        src = self._src()
        js = src.split("<script>")[1].split("</script>")[0]
        for m in _re.finditer(r"for\s*\(([^)]{0,40})", js):
            self.assertTrue(m.group(1).lstrip().startswith("var "),
                            "循环变量须 var 声明（严格模式）: " + m.group(0))

    def test_copy_standard_no_jargon(self):
        """宪法#41：开战/战役/战报不上屏（HTML 段）；按钮=动词+宾语。"""
        html = self._src().split("<script>")[0]
        for bad in ("开战", "战役", "战报", "看战况", "管战场"):
            self.assertNotIn(bad, html, "黑话上屏: " + bad)
        self.assertIn("创建", self._src())

    def test_contact_inline_error_container(self):
        """字段错行内红：⑧联系人容器可指（fi-contact）——失焦校验接线不悬空。"""
        self.assertIn('id="fi-contact"', self._src())

    def test_success_hides_stale_summary(self):
        """成功态：右列实时摘要卡随之隐藏（不留守旧表单回声）。"""
        self.assertIn("col-summary').hidden = true", self._src())

    def test_copy_no_internal_codenames(self):
        """宪法#41+ui-copy-standard-v1：内部工程代号不上屏——HTML 段（剥
        注释）禁 battle-kit（模板数据源名只留注释/后端）；生成文案禁工程词
        与模板仓路径回显。"""
        import re as _re
        src = self._src()
        html = _re.sub(r"<!--.*?-->", "", src.split("<script>")[0], flags=_re.S)
        self.assertNotIn("battle-kit", html, "内部代号上屏: battle-kit")
        no_comment = _re.sub(r"/\*.*?\*/", "", src, flags=_re.S)
        for bad in ("元信息加载失败", "枚举暂缺", "（来源 "):
            self.assertNotIn(bad, no_comment, "工程词/仓路径回显: " + bad)


if __name__ == "__main__":
    unittest.main()
