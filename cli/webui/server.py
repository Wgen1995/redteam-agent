# -*- coding: utf-8 -*-
"""webui server（v0.9a T3）——tanyin-web 只读观察面 HTTP 路由。

法律（docs/design/tanyin-target-form.md §3）：纯 stdlib、ThreadingHTTPServer 线程模型、
禁 asyncio；观察面只读投影（零写入账本）。路由（v0.9a 三分支 + v0.9b 三页）：
  GET /                 → static/index.html（手写仪表盘）
  GET /favicon.ico      → 204 消音（漫游报告 §三4：免每页 console 404）
  GET /api/state.json   → snapshot 快照 JSON
  GET /api/stream       → SSE timeline 追尾流（?tail=N 覆盖存量尾条数）
  GET /coverage|/graph|/evidence            → v0.9b 观察面三页（静态）
  GET /api/matrix|graph|evidence.json       → v0.9b 三只读投影（projections 单源）
  GET /metrics                               → v0.9c 度量页（静态：双臂召回曲线）
  GET /api/metrics.json                      → v0.9c 双臂战例度量（metrics 单源）
  GET /session                               → v0.9d 会话页（静态：战士过程回放只读）
  GET /api/session.json[?battle=N]           → v0.9d 会话投影（session_view 单源；
                                               无参=最新战，?battle=N 选战，坏参 404）
  GET /activity                               → v0.9d 活动流独立页（静态：SSE 追尾）
  GET /experiments                            → v0.9d 302 → /metrics#experiments（度量页锚）
  GET /status.js                              → v0.9d 白名单句柄：仅此一 static 文件外链
                                               （status.js 单源；其余 static 页仍走页面路由）
  GET /login|/new                             → v0.9.8 方向盘两页（登录/新建表单）

v0.9.8 方向盘批——第一批写操作（窄门律，docs/superpowers/plans/2026-10-16-steering-wheel.md）：
  POST /login                                 → 操作员口令（TANYIN_OPERATOR_KEY，缺省随机+banner；
                                               会话 cookie HttpOnly；错 5 锁 60s）
  POST /api/battle/new                        → 新建战斗：授权八问缺一=422（缺授权豁免
                                               通道已废——真授权件先落盘，add-goal 实测 sha 一致才收行）
  POST /api/battle/control                    → pause/resume（b10 指令文件通道）/stop（killpg+EXIT）
                                               /launch（任务书 goals/scope 单源装配+指令基线+runner 点火+留痕）
  POST /api/battle/say                        → 对话指令：指令文件+append-timeline 留痕
  GET  /api/approval                          → 待审只读投影（须会话；附持钥签名）
  POST /api/approval                          → 审批：_approval_sig HMAC（SEC-1）→ approve 落账
  POST /api/report/download                   → 报告产物（缓存命中或触发 render）
写律：一切写入=subprocess 调 tanyin-ledger/tanyin-report 既有命令面（单一写入
路径不破；本模块零账本直写）；守卫=同源+X-Requested-With+会话，缺=401/403 JSON。
启动：cd cli && python -m webui.server --ledger-dir D（T5 接 CLI 入口）。
"""
import datetime
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CLI_DIR not in sys.path:                     # -m/直跑兜底：cli/ 上 path 才有 ledger
    sys.path.insert(0, _CLI_DIR)
# 法律：服务端 import 只来自 stdlib + ledger（本模块只读投影，零账本写入）

from . import snapshot as _snap  # noqa: E402
from . import sse as _sse        # noqa: E402
from . import projections as _proj  # noqa: E402  (v0.9b 三页只读装配)
from . import metrics as _met  # noqa: E402  (v0.9c 度量页只读装配)
from ledger import session_view as _sv  # noqa: E402  (v0.9d 会话页只读装配)
from ledger import battle_registry as _breg  # noqa: E402  (W2·01P0-4 多战仲裁接线)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TAIL = "127.0.0.1", 8900, 50
POLL_S, KEEPALIVE_S = _sse.DEFAULT_POLL_S, _sse.DEFAULT_KEEPALIVE_S


def _session_api(battle):
    """v0.9d 会话 API 装配（session_view 单源）；server_version 单源注入页脚。"""
    out = _sv.session_api(battle=battle)
    out["server_version"] = Handler.server_version
    return out


_PAGE_API = {"/api/matrix.json": _proj.matrix_view,     # v0.9b 三页 API（只读装配单源）
             "/api/graph.json": _proj.graph_view,
             "/api/evidence.json": _proj.evidence_view,
             "/api/metrics.json": (lambda ledger_dir: _met.metrics_view()),  # v0.9c（battles 装配与 ledger 无涉）
             "/api/session.json": (lambda ledger_dir: _session_api(None))}   # v0.9d 无参=最新战


# ===========================================================================
# v0.9.8 方向盘批——门禁 + 五受管写路由（窄门律）
# ===========================================================================
# 铁前提：数据页照旧只读；写=subprocess 调既有命令面（tanyin-ledger/
# tanyin-report），本模块零账本直写（单一写入路径不破）；回执带 timeline 行号。

LEDGER_CLI = os.path.join(_CLI_DIR, "tanyin-ledger")
REPORT_CLI = os.path.join(_CLI_DIR, "tanyin-report")
SESSION_COOKIE = "tanyin_sess"
SESSION_TTL_S = 8 * 3600                  # 会话时长：一个工作班次
LOGIN_MAX_FAILS, LOGIN_LOCK_S = 5, 60     # 错 5 次锁 60s（计划 §第一段）
CTRL_ACTIONS = ("pause", "resume", "stop", "launch")   # W1-T2：launch=点火钮
BATTLE_FORBID_PORTS = (8900, 3000, 8787, 8443)   # W2·01P0-4 平台保留口（webui
#   8900+操作员常驻面 3000/8787/8443）——战斗端口申报禁碰（battle_registry 同表）
BATTLE_BUDGET_CAP_ENV = "TANYIN_BATTLE_BUDGET_CAP_USD"   # 缺省不设帽=登记仍在
APPROVE_DECISIONS = ("approved", "rejected", "exempted")
GEN_OF_NEW_BATTLE = "G-w1"               # 方向盘新战代名（battle.py --gen 同位）
WALL_PHASE_LIFECYCLE = "P-lifecycle"     # battle.py WALL_PHASE 先例：跨阶段控制事件轨
RUNNER_TSV = "opencode-run.log.runner.tsv"
DIRECTIVE_TXT = "directive.txt"
MISSION_TXT = "mission.txt"                  # W1-T2：launch 任务书（goals/scope 行单源装配）
RUNNER_LOG = "opencode-run.log"             # battle.py paths 同名位
ASK_MD = "ask.md"
RUNNER_OUT = "runner.out"
RUNNER_CLI = os.path.join(_CLI_DIR, "tanyin-runner")
_REPO_ROOT = os.path.dirname(_CLI_DIR)      # battle.py ROOT 同位（runner --cwd）


def _utc_now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _approval_sig(command_hash, key_text):
    """SEC-1 同式（write_cmds._approval_sig 单源语义）：
    HMAC-SHA256(key=sha256(key), msg=command_hash)。"""
    return hmac.new(hashlib.sha256(key_text.encode("utf-8")).digest(),
                    command_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def _tl_count(goal_dir):
    """timeline 行数（留痕回执的行号单源：文件实况）。"""
    try:
        with open(os.path.join(goal_dir, "timeline.tsv"), encoding="utf-8") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _run_cli(cli_path, cmd, goal_dir, args, extra_env=None):
    """窄门执行器：subprocess 调既有命令面（唯一写入路径）。
    extra_env：操作员侧密钥仅注入对应子进程（SEC-1：钥不落页面不落盘）。"""
    argv = [sys.executable, cli_path, cmd, "--goal-dir", str(goal_dir)] + list(args)
    env = dict(os.environ)
    env.update(extra_env or {})
    return subprocess.run(argv, capture_output=True, text=True, timeout=120,
                          env=env)


def _ledger_receipt(cmd, goal_dir, args):
    """跑一条 ledger 写命令 → 回执 {cmd, rc, id, timeline_row, out}。"""
    cp = _run_cli(LEDGER_CLI, cmd, goal_dir, args)
    rid = ""
    first = (cp.stdout or "").splitlines()
    if first and first[0].startswith("OK\t"):
        rid = first[0].split("\t")[1]
    return {"cmd": cmd, "rc": cp.returncode, "id": rid,
            "timeline_row": _tl_count(goal_dir),
            "out": ((cp.stdout or "") + (cp.stderr or "")).strip()[:400]}


def _battles_root(server):
    return server.battles_dir or _sv.default_battles_dir()   # session_view 同源


def _breg_verdict_brief(verdict):
    """仲裁拒决人话摘要（数学披露：used/demand/cap 原数入体——可审计）。"""
    if verdict.get("reason") == "budget-cap":
        return "在册预算 %.6g + 申报 %.6g = %.6g > 帽 %.6g" % (
            verdict.get("budget_used", 0.0),
            verdict.get("budget_demand", 0.0) - verdict.get("budget_used", 0.0),
            verdict.get("budget_demand", 0.0), verdict.get("budget_cap", 0.0))
    if verdict.get("reason") == "already-registered":
        return "战在册未出（先 stop 释放再点火；死 pid 册自愈回收）"
    if verdict.get("conflict_ports"):
        return "端口冲突/保留: %s" % verdict["conflict_ports"]
    return str(verdict.get("reason", ""))


def _battle_home(server, battle_no):
    return os.path.join(_battles_root(server), "battle-%d" % battle_no)


def _norm_battle(value):
    """battle 参数归一为 int；不可解析=None。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    s = str(value or "")
    if s.startswith("battle-"):
        s = s[7:]
    return int(s) if s.isdigit() else None


def _latest_gen(battle_home):
    """战目录内最新代目录（G-* 自然序：G-r9 < G-r43）；无=None。"""
    def _key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    try:
        gens = [d for d in os.listdir(battle_home)
                if d.startswith("G-") and os.path.isdir(os.path.join(battle_home, d))]
    except OSError:
        return None
    if not gens:
        return None
    return os.path.join(battle_home, sorted(gens, key=_key)[-1])


def _write_directive(battle_home, text):
    """复用 b10 介入通道：指令文件整文替换（digest 变化触发 runner
    kill+带令续跑；runner 自记 DIRECTIVE 行——零自造事件）。"""
    path = os.path.join(battle_home, DIRECTIVE_TXT)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _last_warrior_pid(battle_home):
    """runner.tsv 最近 LAUNCH/RESTART 行的战士 pid（battle.py last_launch_pid 同式）。"""
    path = os.path.join(battle_home, RUNNER_TSV)
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    for ln in reversed(lines[-30:]):
        if "\tLAUNCH\t" in ln or "\tRESTART\t" in ln:
            for tok in ln.replace("(", " ").split():
                if tok.startswith("pid="):
                    try:
                        return int(tok[4:])
                    except ValueError:
                        pass
    return None


def _find_runner_pids(battle_home):
    """pgrep 实勘 runner 进程（--ledger-dir 指向该战目录；边界钉防 battle-N1 误配）。
    pgrep 缺席/失败=空表（如实披露，不硬造）。"""
    pat = r"tanyin-runner.*--ledger-dir " + re.escape(battle_home) + r"([/ ]|$)"
    try:
        cp = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True, timeout=10)
        if cp.returncode != 0:
            return []
        return [int(x) for x in cp.stdout.split() if x.isdigit()]
    except (OSError, subprocess.SubprocessError):
        return []


def _kill_group(pid):
    """tanyin-runner kill_group 同式：进程组 SIGKILL，退化为单杀。"""
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, signal.SIGKILL)
            return True
        except OSError:
            return False


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ---------------- W1-T1/T2：授权八问校验 + 任务书装配 + runner 点火 -------------

_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_MODEL_TIERS = ("strong", "weak")
_GUARD_TIERS = ("T1", "T2", "T3")


def _iso_z(v):
    """YYYY-MM-DDTHH:MM:SSZ 严格形（范围真解析；write_cmds._ts_range_check 同纪律）。"""
    s = str(v or "")
    if not _ISO_Z_RE.match(s):
        return None
    try:
        datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return s


def _safe_doc_name(filename):
    """授权件落盘名消毒：剥路径只留 basename（防穿越出 goal 目录/覆盖 tsv）。"""
    name = os.path.basename(str(filename or "").replace("\\", "/")).strip()
    if not name or name in (".", "..") or name.endswith(".tsv"):
        return ""
    return name


def _auth_eight_questions(body):
    """授权八问校验（W1-T1）：缺一=（中文拒因, None）；全过=（"", auth 结构化 dict）。
    ①授权文件（原件字节+sha256+签署方）②窗口期 ③范围 ④OOB 联系人 ⑤预算
    ⑥凭据来源 ⑦强度档 ⑧法律条款勾选——豁免通道已废，不再伪造授权四件。"""
    auth = body.get("auth")
    if not isinstance(auth, dict):
        return "授权八问 ①缺授权文件：须上传授权原件（表单 auth 件缺席）", None
    filename = str(auth.get("filename") or "").strip()
    sha256 = str(auth.get("sha256") or "").strip()
    signer = str(auth.get("signer") or "").strip()
    content_b64 = auth.get("content_b64")
    if not filename or not sha256 or not content_b64:
        return "授权八问 ①缺授权文件：文件名/sha256/原件字节（content_b64）缺一不可", None
    if not _HEX64_RE.match(sha256):
        return "授权八问 ①授权文件 sha256 非 64 位 hex", None
    import base64 as _b64
    try:
        doc_bytes = _b64.b64decode(str(content_b64), validate=True)
    except (ValueError, TypeError):
        return "授权八问 ①授权文件原件字节（content_b64）非合法 base64", None
    if not doc_bytes:
        return "授权八问 ①授权文件原件为空字节", None
    if not signer:
        return "授权八问 ①授权文件缺签署方（signer）", None
    safe = _safe_doc_name(filename)
    if not safe:
        return "授权八问 ①授权文件名不可用作落盘名: %s" % filename, None
    valid_from = _iso_z(auth.get("valid_from"))
    valid_until = _iso_z(auth.get("valid_until"))
    if not valid_from or not valid_until:
        return ("授权八问 ②授权窗口期缺或格式不认（须 2026-10-18T00:00:00Z 形）: "
                "%s → %s" % (auth.get("valid_from"), auth.get("valid_until")), None)
    if valid_until <= valid_from:
        return "授权八问 ②授权窗口期非法：valid_until<=valid_from", None
    scope = body.get("scope")
    if not isinstance(scope, list) or not [s for s in scope if str(s).strip()]:
        return "授权八问 ③范围白名单缺：至少一条（无范围的测试一律不开）", None
    contact = str(body.get("emergency_contact") or "").strip()
    if not contact:
        return "授权八问 ④缺 OOB 紧急联系人（授权方 7×24 可达通道）", None
    budget = str(body.get("budget") or "").strip()
    if not budget:
        return "授权八问 ⑤缺预算硬顶（token;requests;hours 三段）", None
    cred_source = str(body.get("cred_source") or "").strip()
    if not cred_source:
        return "授权八问 ⑥缺凭据来源（测试账号从哪来：客户提供/自注册/无凭据探测）", None
    model_tier = str(body.get("model_tier") or "").strip()
    guard_tier = str(body.get("guard_tier") or "").strip()
    if model_tier not in _MODEL_TIERS or guard_tier not in _GUARD_TIERS:
        return ("授权八问 ⑦强度档缺或非枚举（model_tier 须 strong|weak、"
                "guard_tier 须 T1|T2|T3）: %s/%s" % (model_tier, guard_tier)), None
    if body.get("legal_ack") is not True:
        return "授权八问 ⑧法律条款未勾选（legal_ack 须真布尔 true）", None
    out = {"doc_name": safe, "sha256": sha256.lower(), "doc_bytes": doc_bytes,
           "signer": signer, "valid_from": valid_from, "valid_until": valid_until}
    return "", out


def _mission_text(battle_no, goal_dir):
    """launch 任务书：goals/scope 记录行单源装配（目标/预算/授权/范围入文，不虚构）。"""
    from ledger import core as _core

    def col(tname, r, k):
        return r[_core.TABLES[tname].index(k)]

    s = _core.Session(goal_dir)
    lines = ["【GraphLed 任务书】battle-%d（自 goals/scope 记录行单源装配，不虚构）" % battle_no,
             "按授权对以下目标执行渗透测试；授权外的资产一律不碰，预算触顶即停。", ""]
    for g in s.rows("goals.tsv"):
        lines.append("目标：%s" % col("goals.tsv", g, "target"))
        if col("goals.tsv", g, "objective"):
            lines.append("说明：%s" % col("goals.tsv", g, "objective"))
        lines.append("授权：%s 签署，窗口 %s 至 %s（授权件 %s，sha256=%s）"
                     % (col("goals.tsv", g, "signer"),
                        col("goals.tsv", g, "valid_from"),
                        col("goals.tsv", g, "valid_until"),
                        col("goals.tsv", g, "auth_doc"),
                        col("goals.tsv", g, "auth_sha256")))
        if col("goals.tsv", g, "emergency_contact"):
            lines.append("OOB 紧急联系人：%s" % col("goals.tsv", g, "emergency_contact"))
        lines.append("预算硬顶：%s（令牌;请求数;小时数）" % col("goals.tsv", g, "budget"))
        if col("goals.tsv", g, "business_context"):
            lines.append("背景：%s" % col("goals.tsv", g, "business_context"))
        lines.append("强度档：model=%s guard=%s" % (col("goals.tsv", g, "model_tier"),
                                                    col("goals.tsv", g, "guard_tier")))
    lines.append("")
    lines.append("范围（scope 记录行）：")
    for r in s.rows("scope.tsv"):
        lines.append("- [%s] %s%s" % (col("scope.tsv", r, "kind"),
                                      col("scope.tsv", r, "matcher"),
                                      ("（%s）" % col("scope.tsv", r, "note"))
                                      if col("scope.tsv", r, "note") else ""))
    if not s.rows("scope.tsv"):
        lines.append("（无 scope 行——按授权窗口与目标面自律）")
    lines.append("")
    lines.append("每一步写入均留痕可查；发现须附可重放证据；到窗或触顶自动收口。")
    return "\n".join(lines) + "\n"


def _runner_argv(battle_home, goal_dir):
    """runner 参数表（battle.py cmd_launch 同参式：tanyin-runner start 全参）。"""
    return [sys.executable, RUNNER_CLI, "start",
            "--cwd", _REPO_ROOT,
            "--prompt-file", os.path.join(battle_home, MISSION_TXT),
            "--log", os.path.join(battle_home, RUNNER_LOG),
            "--ledger-dir", goal_dir,
            "--max-restarts", "3", "--stall-min", "8",
            "--soft-stall-min", "3", "--backoff-base", "30",
            "--directive-file", os.path.join(battle_home, DIRECTIVE_TXT),
            "--ask-file", os.path.join(battle_home, ASK_MD)]


def _spawn_runner(battle_home, goal_dir):
    """点火 runner（battle.py 同式：新会话组+输出收 runner.out）；返回 pid。"""
    env = dict(os.environ, TANYIN_ANCHOR_AUTO="1")
    kw = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" \
        else {"start_new_session": True}
    with open(os.path.join(battle_home, RUNNER_OUT), "a", encoding="utf-8") as out:
        proc = subprocess.Popen(_runner_argv(battle_home, goal_dir),
                                stdout=out, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, cwd=_REPO_ROOT, env=env, **kw)
    return proc.pid


class Handler(BaseHTTPRequestHandler):
    server_version = "tanyin-web/0.9d"
    protocol_version = "HTTP/1.1"
    timeout = 60                                  # 空闲 keep-alive 连接回收（SSE 写循环不受影响）

    # B舰 P0 修（读面零鉴权）: do_GET 全读面过登录门（写面同源会话校验）。
    # 例外仅 /login（登录页自身）与 /favicon.ico（204 消音，无数据）；
    # 未登录：页路由 302 跳 /login，API/SSE 401 JSON。
    _OPEN_GET = ("/login", "/favicon.ico")
    _PAGE_GET = ("/", "/coverage", "/graph", "/evidence", "/metrics",
                 "/session", "/activity", "/new", "/experiments", "/status.js")

    def log_message(self, fmt, *args):           # 静默（长连接轮询会刷屏；env 开话痨）
        if os.environ.get("TANYIN_WEBUI_DEBUG"):
            sys.stderr.write("[webui] %s\n" % (fmt % args))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path not in self._OPEN_GET and not self._session_ok():
            if u.path in self._PAGE_GET:            # 页路由：带去登录（回来自动回原页由 /login 承担）
                self.send_response(302)
                self.send_header("Location", "/login")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self._fail(401, {"error": "未登录或会话过期——读面须操作员会话"})
        if u.path == "/":
            return self._serve_page("index.html")
        if u.path == "/favicon.ico":                       # 漫游报告 §三4：favicon 消音
            self.send_response(204)                        # 204 无 body——单点根治五页 404
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path == "/status.js":                         # E3 白名单：仅此一文件出 static
            try:
                with open(os.path.join(STATIC_DIR, "status.js"), "rb") as f:
                    self._send(200, "application/javascript; charset=utf-8", f.read())
            except OSError:
                self._send(404, "text/plain; charset=utf-8", b"404 not found\n")
            return
        if u.path in ("/coverage", "/graph", "/evidence",
                      "/metrics", "/session", "/activity"):        # v0.9d 增会话页+活动流页
            return self._serve_page(u.path.lstrip("/") + ".html")
        if u.path in ("/login", "/new"):                         # v0.9.8 方向盘两页
            return self._serve_page(u.path.lstrip("/") + ".html")
        if u.path == "/api/approval":                            # v0.9.8 待审投影（须会话）
            return self._serve_approval_get(u)
        if u.path == "/experiments":                               # v0.9d 度量页锚 302（nav 八链）
            self.send_response(302)
            self.send_header("Location", "/metrics#experiments")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path == "/api/session.json" and "battle" in urllib.parse.parse_qs(u.query):
            return self._serve_session_battle(u)   # v0.9d ?battle=N 选战（表项=无参最新）
        if u.path in _PAGE_API:                                    # 页 API 单源表（v0.9b+v0.9c+v0.9d）
            return self._serve_json(_PAGE_API[u.path](self.server.ledger_dir))
        if u.path == "/api/state.json":
            return self._serve_state()
        if u.path == "/api/stream":
            return self._serve_stream(u)
        self._send(404, "text/plain; charset=utf-8", b"404 not found\n")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_page(self, name):
        try:
            with open(os.path.join(STATIC_DIR, name), "rb") as f:
                body = f.read()
        except OSError:
            return self._send(500, "text/plain; charset=utf-8",
                              name.encode("ascii", "ignore") + b" missing\n")
        self._send(200, "text/html; charset=utf-8", body)

    def _serve_json(self, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(200, "application/json", data)

    def _serve_state(self):
        self._serve_json(_snap.snapshot(self.server.ledger_dir, tail=self.server.tail))

    def _serve_session_battle(self, u):
        """v0.9d 会话选战分支：?battle=N（非数/不存在 → 404 JSON，错误态分流）。"""
        q = urllib.parse.parse_qs(u.query)
        raw = q["battle"][0]
        if not raw.isdigit():
            return self._send(404, "application/json",
                              json.dumps({"error": "battle 战号须整数: " + raw},
                                         ensure_ascii=False).encode("utf-8"))
        payload = _session_api(int(raw))
        if "error" in payload:
            return self._send(404, "application/json",
                              json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        self._serve_json(payload)

    def _serve_stream(self, u):
        q = urllib.parse.parse_qs(u.query)
        tail = self.server.tail
        if "tail" in q and q["tail"][0].isdigit():
            tail = int(q["tail"][0])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")     # 代理禁缓冲（SSE 直通）
        self.send_header("Connection", "close")         # 无限流无长度：帧后即断语义
        self.end_headers()
        self.close_connection = True
        path = os.path.join(self.server.ledger_dir, "timeline.tsv")
        try:
            for fr in _sse.events(path, start_tail=tail,
                                  poll_interval=self.server.poll_s,
                                  keepalive_s=self.server.keepalive_s,
                                  stop=lambda: self.server.stopping):
                self.wfile.write(fr.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
                socket.timeout, OSError):
            pass    # 客户端断开即收尾（写失败=断连的唯一直通信号）

    # ---------------- v0.9.8 方向盘：POST 写面（守卫→窄门→留痕回执） ---------

    _WRITE_ROUTES = ("/api/battle/new", "/api/battle/control", "/api/battle/say",
                     "/api/approval", "/api/report/download")

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/login":
            return self._post_login()
        if u.path in self._WRITE_ROUTES:
            if not self._guard_write():
                return                              # 守卫已回 401/403 JSON
            if u.path == "/api/battle/new":
                return self._post_battle_new()
            if u.path == "/api/battle/control":
                return self._post_battle_control()
            if u.path == "/api/battle/say":
                return self._post_battle_say()
            if u.path == "/api/approval":
                return self._post_approval()
            if u.path == "/api/report/download":
                return self._post_report_download()
        self._send(404, "application/json",
                   json.dumps({"error": "未知路由: " + u.path},
                              ensure_ascii=False).encode("utf-8"))

    # ---- 守卫与会话 ----

    def _read_json(self):
        """读请求体 JSON；坏体=None（调用方回 400）。"""
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        raw = self.rfile.read(n) if n > 0 else b""
        if not raw:
            return {}
        try:
            out = json.loads(raw.decode("utf-8"))
            return out if isinstance(out, dict) else None
        except (ValueError, UnicodeDecodeError):
            return None

    def _fail(self, code, payload):
        self._send(code, "application/json",
                   json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        return False

    def _same_origin(self):
        """同源检查：Origin/Referer 在场必须与 Host 同源（缺省放行——
        自定义头检查是主 CSRF 面，此处兜跨站表单）。"""
        host = self.headers.get("Host") or ""
        for h in ("Origin", "Referer"):
            v = self.headers.get(h) or ""
            if not v:
                continue
            try:
                netloc = urllib.parse.urlparse(v).netloc
            except ValueError:
                return False
            if netloc and host and netloc != host:
                return False
        return True

    def _guard_csrf(self):
        """CSRF 双检：同源 + X-Requested-With 自定义头（写路由一律 POST+JSON）。"""
        if not self._same_origin():
            return self._fail(403, {"error": "拒：跨源请求（CSRF 防护）"})
        if self.headers.get("X-Requested-With") != "XMLHttpRequest":
            return self._fail(403, {"error": "拒：缺 X-Requested-With 头（CSRF 防护）"})
        return True

    def _session_sid(self):
        raw = self.headers.get("Cookie") or ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == SESSION_COOKIE:
                return v
        return ""

    def _session_ok(self):
        sid = self._session_sid()
        exp = self.server.sessions.get(sid)
        return bool(sid and exp and time.time() < exp)

    def _guard_write(self):
        """写路由守卫：会话→401；同源+自定义头→403（顺序=先身份后请求形）。"""
        if not self._session_ok():
            return self._fail(401, {"error": "未登录或会话过期——写操作须操作员会话"})
        return self._guard_csrf()

    # ---- 门禁：/login ----

    def _post_login(self):
        if not self._guard_csrf():
            return
        body = self._read_json()
        if body is None:
            return self._fail(400, {"error": "请求体须 JSON"})
        srv = self.server
        with srv.gate():                            # 错5锁60s：计数串行化
            if time.time() < srv.login_locked_until:
                return self._fail(429, {"error": "口令错误次数过多，已锁定 60 秒",
                                        "retry_after_s": int(srv.login_locked_until - time.time()) + 1})
            password = str(body.get("password") or "")
            if not hmac.compare_digest(password, srv.operator_key):
                srv.login_fails += 1
                if srv.login_fails >= LOGIN_MAX_FAILS:
                    srv.login_fails = 0
                    srv.login_locked_until = time.time() + LOGIN_LOCK_S
                return self._fail(401, {"error": "操作员口令不符"})
            srv.login_fails = 0
        sid = secrets.token_hex(16)
        srv.sessions[sid] = time.time() + SESSION_TTL_S
        # 过期清扫（顺路；量级=登录频次，零额外线程）
        now = time.time()
        for k in [k for k, v in srv.sessions.items() if v < now]:
            del srv.sessions[k]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie",
                         "%s=%s; Path=/; HttpOnly; SameSite=Strict; Max-Age=%d"
                         % (SESSION_COOKIE, sid, SESSION_TTL_S))
        body_out = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", str(len(body_out)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body_out)

    # ---- 钮 1：/api/battle/new ----

    def _post_battle_new(self):
        body = self._read_json()
        if body is None:
            return self._fail(400, {"error": "请求体须 JSON"})
        name = str(body.get("name") or "").strip()
        note = str(body.get("note") or "").strip()
        budget = str(body.get("budget") or "").strip()
        scope = body.get("scope")
        if not name:
            return self._fail(422, {"error": "任务名称必填"})
        # W1-T1 授权八问（场景占位豁免通道已废：本路由只收真授权件）
        err, auth = _auth_eight_questions(body)
        if err:
            return self._fail(422, {"ok": False, "error": err})
        root = _battles_root(self.server)
        try:
            nums = [int(m.group(1)) for e in os.listdir(root)
                    for m in [re.match(r"^battle-(\d+)$", e)] if m]
        except OSError:
            nums = []
        n = (max(nums) + 1) if nums else 1
        home = os.path.join(root, "battle-%d" % n)
        gd = os.path.join(home, GEN_OF_NEW_BATTLE)
        os.makedirs(gd, exist_ok=True)
        # ①授权原件先落盘（消毒名）；add-goal 真校验链随后实测 sha——一致才收行
        with open(os.path.join(gd, auth["doc_name"]), "wb") as f:
            f.write(auth["doc_bytes"])
        ts = _utc_now()
        context = "凭据来源：" + str(body.get("cred_source") or "").strip()
        if note:
            context += "；说明：" + note
        receipts = [_ledger_receipt("add-goal", gd, [
            "--target=" + name, "--objective=" + (note or "（观察面开战，未填说明）"),
            "--auth-doc=" + auth["doc_name"], "--auth-sha256=" + auth["sha256"],
            "--signer=" + auth["signer"],
            "--valid-from=" + auth["valid_from"], "--valid-until=" + auth["valid_until"],
            "--emergency-contact=" + str(body.get("emergency_contact") or "").strip(),
            "--budget=" + budget,
            "--business-context=" + context,
            "--model-tier=" + str(body.get("model_tier") or "").strip(),
            "--guard-tier=" + str(body.get("guard_tier") or "").strip(),
            "--timestamp=" + ts])]
        if receipts[0]["rc"] != 0:
            # 立项即拒=整战不落（清空本次新建的空目录，防占号留壳）
            import shutil
            if not os.path.exists(os.path.join(gd, "goals.tsv")):
                shutil.rmtree(home, ignore_errors=True)
            return self._fail(422, {"ok": False, "error": "立项被拒：" + receipts[0]["out"],
                                    "ledger": receipts})
        for s in scope:
            m = str(s).strip()
            if not m:
                continue
            receipts.append(_ledger_receipt("add-scope", gd, [
                "--kind=include", "--matcher=" + m, "--note=开战表单白名单",
                "--timestamp=" + ts]))
        ok = all(r["rc"] == 0 for r in receipts)
        payload = {"ok": ok, "battle": n, "goal_dir": gd,
                   "goal_id": receipts[0]["id"], "ledger": receipts,
                   "auth_doc": auth["doc_name"],
                   "timeline_rows": _tl_count(gd)}
        if not ok:
            payload["error"] = "部分范围行被拒（详见 ledger 回执）"
            return self._fail(422, payload)
        self._serve_json(payload)

    # ---- 钮 2：/api/battle/control ----

    def _post_battle_control(self):
        body = self._read_json()
        if body is None:
            return self._fail(400, {"error": "请求体须 JSON"})
        n = _norm_battle(body.get("battle"))
        action = str(body.get("action") or "")
        if n is None:
            return self._fail(422, {"error": "battle 须战号（整数）"})
        if action not in CTRL_ACTIONS:
            return self._fail(422, {"error": "action 须 pause|resume|stop|launch"})
        home = _battle_home(self.server, n)
        if not os.path.isdir(home):
            return self._fail(404, {"error": "战目录不存在: battle-%d" % n})
        gd = _latest_gen(home)
        if gd is None:
            return self._fail(404, {"error": "battle-%d 无记录目录（G-*）——先立项" % n})
        ts = _utc_now()
        if action == "launch":
            # W1-T2 点火钮：已在跑=拒 → 任务书（无则装配，人工改过不覆盖）→
            # 指令基线（空文件=digest 基线，battle.py 同式）→ runner spawn → 留痕
            live = _find_runner_pids(home)
            if live:
                return self._fail(422, {"ok": False,
                                        "error": "battle-%d 已在跑（runner pid=%s）——"
                                                 "先 stop 再点火，不许双跑"
                                                 % (n, ",".join(str(p) for p in live))})
            # W2·01P0-4 多战仲裁接线：battles 根在册（预算帽+在册互斥）——册比
            # pid 扫描保守（扫描扑空而在册行活=fail-closed 拒双跑）；申报额
            # 请求体 budget_usd（缺省 0），帽=TANYIN_BATTLE_BUDGET_CAP_USD（缺省
            # 不设帽·登记仍在）；拒绝判决带数学披露原样回体（可审计）。
            try:
                budget_usd = float(body.get("budget_usd") or 0.0)
            except (TypeError, ValueError):
                budget_usd = -1.0
            if not (budget_usd >= 0.0):   # NaN 同拒（负/NaN 申报=输入域 422）
                return self._fail(422, {"ok": False,
                                        "error": "budget_usd 须非负数（多战预算申报）"})
            cap_raw = os.environ.get(BATTLE_BUDGET_CAP_ENV)
            cap = None
            if cap_raw not in (None, ""):
                try:
                    cap = float(cap_raw)
                except ValueError:
                    return self._fail(422, {"ok": False, "error":
                                            "环境 %s 须数字: %r"
                                            % (BATTLE_BUDGET_CAP_ENV, cap_raw)})
            verdict = _breg.admit(_battles_root(self.server), "battle-%d" % n,
                                  budget_usd=budget_usd, cap_budget_usd=cap,
                                  forbid_ports=BATTLE_FORBID_PORTS)
            if not verdict["allowed"]:
                return self._fail(422, {"ok": False,
                                        "error": "多战仲裁拒（%s）——%s"
                                                 % (verdict["reason"],
                                                    _breg_verdict_brief(verdict)),
                                        "verdict": verdict})
            mission = os.path.join(home, MISSION_TXT)
            if not os.path.isfile(mission):
                with open(mission, "w", encoding="utf-8") as f:
                    f.write(_mission_text(n, gd))
            directive = os.path.join(home, DIRECTIVE_TXT)
            if not os.path.isfile(directive):
                with open(directive, "w", encoding="utf-8") as f:
                    f.write("")
            pid = _spawn_runner(home, gd)
            _breg.set_pid(_battles_root(self.server), "battle-%d" % n, pid)
            r = _ledger_receipt("append-timeline", gd, [
                "--actor=人工", "--phase=" + WALL_PHASE_LIFECYCLE,
                "--event=battle-launch battle-%d runner-pid=%d mission=%s"
                % (n, pid, MISSION_TXT),
                "--timestamp=" + ts])
            if r["rc"] != 0:
                return self._fail(422, {"ok": False, "error": "留痕被拒：" + r["out"],
                                        "ledger": r})
            return self._serve_json({"ok": True, "action": "launch", "battle": n,
                                     "runner_pid": pid, "mission": mission,
                                     "timeline_row": r["timeline_row"],
                                     "note": "引擎已点火；任务书=mission.txt，"
                                             "指令通道=directive.txt"})
        if action in ("pause", "resume"):
            word = "暂停" if action == "pause" else "恢复"
            text = ("【操作员%s令】时间 %s 说明：操作员经观察面下达%s。"
                    % (word, ts, word))
            if action == "pause":
                text += "完成当前步骤后停止新的探测动作，等待恢复令。"
            else:
                text += "从中断处继续执行，勿重复已落账条目。"
            _write_directive(home, text)
            r = _ledger_receipt("append-timeline", gd, [
                "--actor=人工", "--phase=" + WALL_PHASE_LIFECYCLE,
                "--event=battle-%s battle-%d directive-len=%d" % (action, n, len(text)),
                "--timestamp=" + ts])
            if r["rc"] != 0:
                return self._fail(422, {"ok": False, "error": "留痕被拒：" + r["out"],
                                        "ledger": r})
            return self._serve_json({"ok": True, "action": action, "battle": n,
                                     "directive": "written", "timeline_row": r["timeline_row"],
                                     "note": "指令已入通道；runner 下轮巡检即带令续跑"})
        # stop：先停 runner（防复活）→再停战士组→EXIT 行→留痕
        runner_pids = _find_runner_pids(home)
        runner_killed = bool(runner_pids)
        for pid in runner_pids:
            if not _kill_group(pid):
                runner_killed = False
        wpid = _last_warrior_pid(home)
        warrior_killed = False
        if wpid is not None and _pid_alive(wpid):
            warrior_killed = _kill_group(wpid)
        with open(os.path.join(home, RUNNER_TSV), "a", encoding="utf-8") as f:
            f.write("%s\tEXIT\toperator-stop runner=%s warrior=%s\n"
                    % (ts, ",".join(str(p) for p in runner_pids) or "none",
                       wpid if wpid is not None else "none"))
        released = _breg.release(_battles_root(self.server), "battle-%d" % n)
        r = _ledger_receipt("append-timeline", gd, [
            "--actor=人工", "--phase=" + WALL_PHASE_LIFECYCLE,
            "--event=battle-stop battle-%d runner=%d warrior=%s"
            % (n, len(runner_pids), wpid if wpid is not None else "none"),
            "--timestamp=" + ts])
        if r["rc"] != 0:
            return self._fail(422, {"ok": False, "error": "留痕被拒：" + r["out"],
                                    "ledger": r,
                                    "runner_killed": runner_killed,
                                    "warrior_killed": warrior_killed})
        return self._serve_json({"ok": True, "action": "stop", "battle": n,
                                 "runner_killed": runner_killed,
                                 "warrior_killed": warrior_killed,
                                 "warrior_pid": wpid,
                                 "released": released or False,
                                 "timeline_row": r["timeline_row"]})

    # ---- 钮 3：/api/battle/say ----

    def _post_battle_say(self):
        body = self._read_json()
        if body is None:
            return self._fail(400, {"error": "请求体须 JSON"})
        n = _norm_battle(body.get("battle"))
        text = str(body.get("text") or "").strip()
        if n is None:
            return self._fail(422, {"error": "battle 须战号（整数）"})
        if not text:
            return self._fail(422, {"error": "指令内容为空"})
        home = _battle_home(self.server, n)
        if not os.path.isdir(home):
            return self._fail(404, {"error": "战目录不存在: battle-%d" % n})
        gd = _latest_gen(home)
        if gd is None:
            return self._fail(404, {"error": "battle-%d 无记录目录（G-*）——先立项" % n})
        _write_directive(home, text)
        ts = _utc_now()
        r = _ledger_receipt("append-timeline", gd, [
            "--actor=人工", "--phase=" + WALL_PHASE_LIFECYCLE,
            "--event=battle-say battle-%d len=%d" % (n, len(text)),
            "--timestamp=" + ts])
        if r["rc"] != 0:
            return self._fail(422, {"ok": False, "error": "留痕被拒：" + r["out"],
                                    "ledger": r})
        self._serve_json({"ok": True, "battle": n, "directive": "written",
                          "timeline_row": r["timeline_row"],
                          "note": "指令已入通道；runner 下轮巡检即带令续跑"})

    # ---- 钮 4：/api/approval ----

    def _approval_projection(self):
        """待审只读投影（单源=cleanup-checklist 同判定：revert 未核销未豁免）。
        复用 ledger.query_cmds._replay_status 纯读推导（服务端只读装配先例）。"""
        from ledger import core as _core, query_cmds as _qc
        s = _core.Session(self.server.ledger_dir)
        tl = s.rows("timeline.tsv")
        idx_rc = _core.TABLES["timeline.tsv"].index("revert_cmd")
        idx_ts = _core.TABLES["timeline.tsv"].index("timestamp")
        idx_ev = _core.TABLES["timeline.tsv"].index("event")
        pending = []
        key = self.server.approval_key
        for it in _qc._replay_status(s):
            if it["status"] != "pending":
                continue
            raw = it["row"]
            row_no = tl.index(raw) + 1
            chash = _sha256_hex(raw[idx_rc])
            pending.append({"row": row_no, "ts": raw[idx_ts], "event": raw[idx_ev],
                            "revert_cmd": raw[idx_rc], "command_hash": chash,
                            "_approval_sig": _approval_sig(chash, key) if key else ""})
        arows = s.rows("approvals.tsv")
        idx_d = _core.TABLES["approvals.tsv"].index("decision")
        idx_t = _core.TABLES["approvals.tsv"].index("timestamp")
        idx_i = _core.TABLES["approvals.tsv"].index("id")
        recent = [{"id": a[idx_i], "decision": a[idx_d], "timestamp": a[idx_t]}
                  for a in arows[-5:]]
        return {"pending": pending, "pending_count": len(pending),
                "key_configured": bool(key), "recent": recent}

    def _serve_approval_get(self, u):
        if not self._session_ok():
            return self._fail(401, {"error": "未登录或会话过期——待审清单须操作员会话"})
        try:
            return self._serve_json(self._approval_projection())
        except Exception as e:                      # 读面容错：坏账不 500
            return self._fail(422, {"error": "待审投影失败: %r" % e})

    def _post_approval(self):
        body = self._read_json()
        if body is None:
            return self._fail(400, {"error": "请求体须 JSON"})
        decision = str(body.get("decision") or "")
        if decision not in APPROVE_DECISIONS:
            return self._fail(422, {"error": "decision 须 approved|rejected|exempted"})
        key = self.server.approval_key
        if not key:
            return self._fail(422, {"error": "审批密钥未配置（TANYIN_APPROVAL_KEY 缺席）"
                                          "——持钥通道关闭，不收审批"})
        from ledger import core as _core
        s = _core.Session(self.server.ledger_dir)
        tl = s.rows("timeline.tsv")
        try:
            row_no = int(body.get("row"))
        except (TypeError, ValueError):
            return self._fail(422, {"error": "row 须待审行号（整数）"})
        if not (1 <= row_no <= len(tl)):
            return self._fail(422, {"error": "row 超出范围: %d" % row_no})
        raw = tl[row_no - 1]
        idx_rc = _core.TABLES["timeline.tsv"].index("revert_cmd")
        idx_ev = _core.TABLES["timeline.tsv"].index("event")
        revert_cmd = raw[idx_rc]
        if not revert_cmd.strip():
            return self._fail(422, {"error": "第 %d 行不是待审行（无清理命令）" % row_no})
        chash = _sha256_hex(revert_cmd)
        sig = str(body.get("_approval_sig") or "")
        if not sig or not hmac.compare_digest(sig, _approval_sig(chash, key)):
            return self._fail(403, {"error": "审批签名缺失或不符（_approval_sig HMAC）"})
        ts = _utc_now()
        note = "%s（观察面审批 行=%d）" % (raw[idx_ev], row_no)
        # 签名转发=钥只进子进程 env（SEC-1 持钥通道开启），账本自验自存 sig 段
        argv = ["--command-hash=" + chash, "--decision=" + decision,
                "--approver=操作员(观察面)", "--timestamp=" + ts,
                "--sig=" + sig, "--note=" + note]
        cp = _run_cli(LEDGER_CLI, "approve", self.server.ledger_dir, argv,
                      extra_env={"TANYIN_APPROVAL_KEY": key})
        first = (cp.stdout or "").splitlines()
        rid = first[0].split("\t")[1] if first and first[0].startswith("OK\t") else ""
        r = {"cmd": "approve", "rc": cp.returncode, "id": rid,
             "timeline_row": _tl_count(self.server.ledger_dir),
             "out": ((cp.stdout or "") + (cp.stderr or "")).strip()[:400]}
        if r["rc"] != 0:
            return self._fail(422, {"ok": False, "error": "审批被拒：" + r["out"],
                                    "ledger": r})
        self._serve_json({"ok": True, "approval_id": r["id"], "row": row_no,
                          "decision": decision, "timeline_row": r["timeline_row"]})

    # ---- 钮 5：/api/report/download ----

    def _post_report_download(self):
        gd = self.server.ledger_dir
        draft = os.path.join(gd, "report", "draft")
        mds = self._draft_mds(draft)
        render_rc = None
        if not mds:                                  # 缺则触发生成（只读聚合产物）
            try:
                cp = _run_cli(REPORT_CLI, "render", gd, ["--all", "--out=" + draft])
                render_rc = cp.returncode
            except subprocess.SubprocessError:
                render_rc = -1
            mds = self._draft_mds(draft)
        if not mds:
            return self._fail(409, {"error": "暂无可下载的报告产物（渲染无果或"
                                              "尚无发现记录）", "render_rc": render_rc})
        if len(mds) == 1:
            name = os.path.basename(mds[0])
            with open(mds[0], "rb") as f:
                data = f.read()
            ctype = "text/markdown; charset=utf-8"
        else:
            name = "report-bundle.zip"
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for p in mds:
                    z.write(p, os.path.basename(p))
            data = buf.getvalue()
            ctype = "application/zip"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", "attachment; filename=%s" % name)
        self.send_header("X-Report-Files", str(len(mds)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _draft_mds(draft):
        try:
            return sorted(os.path.join(draft, e) for e in os.listdir(draft)
                          if e.endswith(".md"))
        except OSError:
            return []


class WebServer(ThreadingHTTPServer):
    daemon_threads = True                          # SSE 长连接随进程收尾

    def __init__(self, addr, handler, ledger_dir=".", tail=DEFAULT_TAIL,
                 poll_s=POLL_S, keepalive_s=KEEPALIVE_S,
                 operator_key=None, approval_key=None, battles_dir=""):
        super().__init__(addr, handler)
        self.ledger_dir = ledger_dir
        self.tail = tail
        self.poll_s = poll_s
        self.keepalive_s = keepalive_s
        self.stopping = False                      # SSE 轮询停机旗
        # v0.9.8 方向盘门禁面（线程锁：ThreadingHTTPServer 并发写计数）
        self._gate_lock = threading.Lock()
        self.operator_key_generated = operator_key in (None, "")
        self.operator_key = (operator_key if operator_key not in (None, "")
                             else secrets.token_urlsafe(12))
        self.approval_key = ((os.environ.get("TANYIN_APPROVAL_KEY", ""))
                             if approval_key is None else approval_key)
        self.battles_dir = battles_dir or ""
        self.sessions = {}                         # sid -> 过期时刻
        self.login_fails = 0
        self.login_locked_until = 0.0

    def gate(self):
        """登录计数/锁的串行化面（错5锁60s 的竞态防护）。"""
        return self._gate_lock

    def handle_error(self, request, client_address):
        """默认静默：客户端未礼别断开（读请求行 ConnectionReset）是浏览器常态噪音；
        TANYIN_WEBUI_DEBUG=1 时走默认回溯打印（排障）。"""
        if os.environ.get("TANYIN_WEBUI_DEBUG"):
            super().handle_error(request, client_address)


def make_server(host=DEFAULT_HOST, port=0, ledger_dir=".", tail=DEFAULT_TAIL,
                poll_s=POLL_S, keepalive_s=KEEPALIVE_S,
                operator_key=None, approval_key=None, battles_dir=""):
    """造服务器（port=0=临时端口，server_address[1] 取实际口）。
    v0.9.8：operator_key 缺省取 TANYIN_OPERATOR_KEY，再缺省随机生成（banner 打印）；
    approval_key 三态：None=取 TANYIN_APPROVAL_KEY 环境值，""=显式无钥。"""
    if operator_key in (None, ""):
        operator_key = os.environ.get("TANYIN_OPERATOR_KEY") or None
    return WebServer((host, port), Handler, ledger_dir, tail, poll_s, keepalive_s,
                     operator_key=operator_key, approval_key=approval_key,
                     battles_dir=battles_dir)


USAGE = ("用法: python -m webui.server --ledger-dir D [--host H] [--port N] "
         "[--tail N] [--help]")


def parse_args(argv):
    """--k=v 与 --k v 双形态归一（tanyin-viz _kv 同款）；--help/-h 裸旗标。
    返回 {ledger_dir,host,port,tail[,help][,error]}；用法错置 error 键（中文理由）。"""
    out = {"ledger_dir": "", "host": DEFAULT_HOST,
           "port": DEFAULT_PORT, "tail": DEFAULT_TAIL}
    kv, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            out["help"] = True
            i += 1
            continue
        if not a.startswith("--"):
            out["error"] = "未知参数: " + a
            return out
        if "=" in a:
            kv[a.split("=", 1)[0]] = a.partition("=")[2]   # 键归一：剥 =值 尾
            i += 1
        elif i + 1 < len(argv):
            kv[a] = argv[i + 1]
            i += 2
        else:
            kv[a] = ""
            i += 1
    out["ledger_dir"] = kv.pop("--ledger-dir", "")
    for flag, key in (("--host", "host"), ("--port", "port"), ("--tail", "tail")):
        if flag in kv:
            out[key] = kv.pop(flag)
    if kv:
        out["error"] = "未知旗标: " + ",".join(sorted(kv))
        return out
    try:
        out["port"] = int(out["port"])
        out["tail"] = int(out["tail"])
    except ValueError:
        out["error"] = "--port/--tail 须整数"
        return out
    if not out["ledger_dir"] and "help" not in out:
        out["error"] = "缺 --ledger-dir"
    return out


def main(argv):
    from ledger.runtime import bootstrap   # v0.7a 装配单源（path 垫片+utf8 stdio）
    bootstrap(__file__)
    kv = parse_args(argv[1:])
    if kv.get("help"):
        print(USAGE)
        return 0
    if kv.get("error"):
        sys.stderr.write(kv["error"] + chr(10) + USAGE + chr(10))
        return 2
    gd = kv["ledger_dir"]
    if not os.path.isdir(gd):
        sys.stderr.write("环境问题: ledger 目录不存在 " + gd + chr(10))
        return 2
    srv = make_server(kv["host"], kv["port"], gd, tail=kv["tail"])
    port = srv.server_address[1]
    print("tanyin-web v0.9.8 方向盘（只读观察+受控写入）: %s:%d/ ledger=%s tail=%d"
          % (kv["host"], port, gd, kv["tail"]))
    if srv.operator_key_generated:                 # 缺省口令=启动随机+banner 披露
        print("操作员口令(本次随机生成，TANYIN_OPERATOR_KEY 可固定): %s"
              % srv.operator_key)
    if srv.approval_key:
        print("审批持钥通道: 已配置（TANYIN_APPROVAL_KEY 在场）")
    else:
        print("审批持钥通道: 未配置（审批卡将拒绝提交——须 TANYIN_APPROVAL_KEY）")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.stopping = True
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
