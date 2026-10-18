# -*- coding: utf-8 -*-
"""api_pages（UI-1 总装舰）——pages/ 统一页路由 + /api/v2/* 统一挂载口。

舰间契约（十件 api_v2_* docstring 已钉，本口照抄 tests/*/_V2MountHandler 挂法）：
  会话门   = 复用 Handler._session_ok（server.py 挂载点先过门再进本口；
             缺会话=401 JSON，页路由 302 /login——server.py 既有门，本模块零门禁）。
  页路由   = GET /p/<slug> 与 /p/<slug>.html（兄弟页相对链接形 new-task.html）
             → static/pages/<slug>.html；slug 合法形 [a-z0-9][a-z0-9-]* 且件在
             盘上才 200，否则 404（不列盘不猜测——空 href 不落页）。
  API 分发 = api_v2_<mod>.dispatch(path, query, ledger_dir[, battles_dir][, kit_dir])
             → (status, payload) | None（非本域路由）；十一件稳定件直挂，
             在飞舰可选件（settings/workspace/evals）guarded import——半成品
             不拖垮整机，落成即自动并网。单件投影异常=500 JSON（带舰名可审计），
             绝不让异常炸穿 ThreadingHTTPServer 连接层。
  POST 分发 = api_v2_<mod>.dispatch_post(path, body, ledger_dir)（仅 settings 舰有）；
             守卫（会话+同源+X-Requested-With）在 server.py 挂载点统一过。

导航网单源 = static/app.js NAV（客户端）；本模块不造第二份——tests 用
test_webui_mount_all.py 解析 app.js 对照盘上页面件（防断链）。
"""
import importlib
import inspect
import os
import re

from . import api_v2_approval_center   # noqa: F401  (稳定件·十舰+技法/复测)
from . import api_v2_asset_registry    # noqa: F401
from . import api_v2_assets            # noqa: F401
from . import api_v2_broadcast         # noqa: F401
from . import api_v2_coverage          # noqa: F401
from . import api_v2_findings          # noqa: F401
from . import api_v2_guard             # noqa: F401
from . import api_v2_reports           # noqa: F401
from . import api_v2_retest            # noqa: F401
from . import api_v2_tasks             # noqa: F401
from . import api_v2_techniques        # noqa: F401

# 在飞舰可选件（未提交/半成品允许缺席——import 失败/形不合=静默跳过不并网；
# 落成即自动并网，总装不逼等任何一舰）
_OPTIONAL_MODULES = ("api_v2_settings", "api_v2_workspace", "api_v2_evals",
                     "api_v2_ask", "api_v2_command", "api_v2_llm",
                     "api_v2_llm_status", "api_v2_system", "api_v2_tools",
                     "api_v2_capability",
                     "api_v2_cockpit",   # 驾驶舱舰（功能27）：四路聚合投影
                     "api_v2_fleet",     # 多任务治理舰（功能25补件）：总控数据面
                     "api_v2_chat")      # 壳重排舰（IA v2）：对话面只读投影

PAGES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "static", "pages")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _v2_modules():
    """稳定件直取 + 可选件 guarded import → [module, ...]（顺序=挂载序）。"""
    mods = [api_v2_approval_center, api_v2_asset_registry, api_v2_assets,
            api_v2_broadcast, api_v2_coverage, api_v2_findings, api_v2_guard,
            api_v2_reports, api_v2_retest, api_v2_tasks, api_v2_techniques]
    for name in _OPTIONAL_MODULES:
        try:
            mod = importlib.import_module("." + name, __package__)
            if not callable(getattr(mod, "dispatch", None)):   # 形不合=未落成
                continue
            mods.append(mod)
        except Exception:                      # 半成品/缺席=不并网（不拖垮整机）
            continue
    return mods


def _bind(mod):
    """dispatch 形参差异（battles_dir/kit_dir 有无）适配成统一调用面。"""
    try:
        params = inspect.signature(mod.dispatch).parameters
    except (TypeError, ValueError):            # 签名不可读=按三位置参兜底
        params = {}
    kw_battles = "battles_dir" in params
    kw_kit = "kit_dir" in params

    def call(path, query, ledger_dir, battles_dir, kit_dir):
        kw = {}
        if kw_battles:
            kw["battles_dir"] = battles_dir
        if kw_kit:
            kw["kit_dir"] = kit_dir
        return mod.dispatch(path, query, ledger_dir, **kw)
    return call


_API_MODULES = _v2_modules()
_API_CALLS = [(m.__name__, _bind(m)) for m in _API_MODULES]


def mounted_v2_routes():
    """诊断面：{路由: 模块名}——挂载体检/tests 钉「十件全挂」用（短名不带包前缀）。"""
    out = {}
    for mod in _API_MODULES:
        for path, fn in getattr(mod, "ROUTES", {}).items():
            if fn is not None:
                out[path] = mod.__name__.rsplit(".", 1)[-1]
    return out


def page_file(path):
    """'/p/<slug>'|'/p/<slug>.html' → ('pages/<slug>.html', None)|(None, 中文错因)。"""
    rest = path[len("/p/"):]
    slug = rest[:-5] if rest.endswith(".html") else rest
    if not slug or not _SLUG_RE.match(slug):
        return None, "页名非法（须 a-z0-9 连字符形）: " + slug
    if not os.path.isfile(os.path.join(PAGES_ROOT, slug + ".html")):
        return None, "页面不存在: " + slug
    return "pages/" + slug + ".html", None


def page_slugs():
    """盘上全部页面 slug（导航网体检：app.js 每个 /p/ 链接须在此列）。"""
    try:
        names = os.listdir(PAGES_ROOT)
    except OSError:
        return []
    return sorted(n[:-5] for n in names
                  if n.endswith(".html") and _SLUG_RE.match(n[:-5]))


_JS_SLUG_RE = re.compile(r"^[a-z0-9_][a-z0-9_.-]*\.js$")   # 首字符许下划线(_palette 形)


def pages_asset_file(path):
    """/static/pages/<name>.js → ('pages/<name>.js', None)|(None, 中文错因)。

    命令面板组件（_palette.js，96e10b93 舰）等页级共享 JS 的放行口：
    只收 .js 尾、只认 pages/ 目录盘上实件（防穿越/防借道读 .html）。
    """
    rest = path[len("/static/pages/"):]
    if not _JS_SLUG_RE.match(rest):
        return None, "页级资产不存在（只放行 pages/*.js）: " + rest
    if not os.path.isfile(os.path.join(PAGES_ROOT, rest)):
        return None, "页级资产不存在: " + rest
    return "pages/" + rest, None


def api_v2_dispatch(path, query, ledger_dir, battles_dir=None, kit_dir=None):
    """/api/v2/* 统一分发 → (status, payload) | None（非本域路由/全舰不识）。"""
    if not path.startswith("/api/v2/"):
        return None
    for name, call in _API_CALLS:
        try:
            res = call(path, query, ledger_dir, battles_dir, kit_dir)
        except Exception as e:                 # 单舰炸=500 JSON，不炸穿连接层
            return 500, {"error": "api_v2 投影失败(%s): %r" % (name, e)}
        if res is not None:
            return res
    return None


def api_v2_post_dispatch(path, body, ledger_dir):
    """/api/v2/* POST 统一分发（可选件才有 POST 面；守卫已在挂载点过）。"""
    if not path.startswith("/api/v2/"):
        return None
    for mod in _API_MODULES:
        fn = getattr(mod, "dispatch_post", None)
        if fn is None:
            continue
        try:
            res = fn(path, body, ledger_dir)
        except Exception as e:
            return 500, {"error": "api_v2 写入口失败(%s): %r" % (mod.__name__, e)}
        if res is not None:
            return res
    return None
