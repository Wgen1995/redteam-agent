# -*- coding: utf-8 -*-
"""api_v2_settings（T7·P8-P18 设置页）——账本参数读写面，路由
GET/POST /api/v2/settings.json。

舰间契约：本文件=本舰独写；读投影零写入（一切文件 r 模式 open，禁
datetime.now——读输出确定性）；写路径=窄门 subprocess 调既有
tanyin-ledger amend-scope（唯一写入路径，server._run_cli 同法——本模块不
自己写表，不造第二配置真源）。挂载=ROUTES/POST_ROUTES 单源表由 include
机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_settings.py（_V2MountHandler）：GET 过会话门；
POST 过会话门+CSRF 双检（Handler._guard_csrf）。

落法（A 舰 B62/D8 对齐）：设置页=账本参数的读写面（amendment 语义，
改动=行+因）。档位（goals.tsv model_tier/guard_tier）与预算三元组随任务
声明入账=读面展示（无修订命令=不提供改写——诚实法条）；范围参数
（scope.tsv）=可修订面：amend-scope 行+note（因，空=拒）+P0 后须 approval
（指向 approved 行）——修订链 amendment_of 后行覆盖先行（enforce 契约 05 §3）。

数据单源：goals.tsv（档位/预算三元组/速率窗/语言）+ scope.tsv（修订链）+
approvals.tsv（豁免清单 decision=exempted；P0 后审批 approved）+ timeline
（amend-scope 修订史；P1-P6 行=P0 已过判定——write_cmds._p0_over 同律只读）。
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

from ledger import core
from ledger.session_view import list_battles

ROUTE_SETTINGS = "/api/v2/settings.json"
ROUTES = {ROUTE_SETTINGS: None}                       # 尾部赋真身（前向引用）
POST_ROUTES = {ROUTE_SETTINGS: None}

_TIER_ZH = {"strong": "强", "weak": "弱"}
_KINDS = ("include", "exclude", "oob", "account-grant")
_P_PHASE = re.compile(r"^P[1-6]")
CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_CLI = os.path.join(CLI_DIR, "tanyin-ledger")

_GL = core.TABLES["goals.tsv"]
_SC = core.TABLES["scope.tsv"]
_AP = core.TABLES["approvals.tsv"]
_TL = core.TABLES["timeline.tsv"]
_BU = core.TABLES["budget.tsv"]


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_tsv_rows(path, nfields):
    text = _read_text(path)
    if text is None:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        out.append((cols + [""] * nfields)[:nfields] if len(cols) < nfields else cols)
    return out


def _gens(battle_dir):
    """G-* 子目自然序（G-r2<G-r10；server._latest_gen 同律）；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in re.findall(r"\d+", name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


def _read_int(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None，布尔无语义：%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数：%r" % (name, value))


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir) —— 有战用战，无战回落主账本。"""
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return [], None, str(ledger_dir or "")
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return battles, None, None
    return battles, picked, os.path.join(root, picked["id"])


def _goal_dir_of(battle_dir):
    gens = _gens(battle_dir)
    if gens:
        return os.path.join(battle_dir, gens[-1]), gens[-1]
    return str(battle_dir or ""), os.path.basename(os.path.normpath(str(battle_dir or "")))


def _merged_rows(battle_dir, tname):
    """跨代合并同 id 后行胜（读面口径）→ [cols]。"""
    gens = _gens(battle_dir)
    dirs = [os.path.join(battle_dir, g) for g in gens] if gens else [battle_dir]
    nf = len(core.TABLES[tname])
    by_id, order = {}, []
    for d in dirs:
        if not d:
            continue
        for cols in _read_tsv_rows(os.path.join(d, tname), nf):
            key = cols[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = cols
    return [by_id[k] for k in order]


def _budget_limits(raw):
    """「token;requests;hours」→ {tokens,requests,hours:int|None}（坏段= None）。"""
    out = {"tokens": None, "requests": None, "hours": None}
    seg = (raw or "").split(";")
    for key, val in zip(("tokens", "requests", "hours"), seg):
        try:
            out[key] = int(val)
        except (TypeError, ValueError):
            continue
    return out


def _p0_over(goal_dir):
    """P0 后判定（write_cmds._p0_over 同律，只读）：timeline 出现 P1-P6 即过。"""
    for cols in _read_tsv_rows(os.path.join(goal_dir, "timeline.tsv"), len(_TL)):
        if _P_PHASE.match((cols[2] or "").strip()):
            return True
    return False


# ------------------------------------------------------------------ 读投影 --

def settings_view(battles_dir=None, battle=None, ledger_dir=None):
    """设置页读投影 → {battle, battles, goal, params, budget, scope, counts,
    exemptions, amendment_history, p0_over, writable}。只读零写入。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    goal_dir, goal = _goal_dir_of(battle_dir)

    grows = _read_tsv_rows(os.path.join(goal_dir, "goals.tsv"), len(_GL))
    gi = {f: i for i, f in enumerate(_GL)}
    g0 = grows[0] if grows else [""] * len(_GL)
    params = {
        "target": g0[gi["target"]], "model_tier": g0[gi["model_tier"]],
        "model_tier_zh": _TIER_ZH.get(g0[gi["model_tier"]], "未申报"),
        "guard_tier": g0[gi["guard_tier"]],
        "budget": g0[gi["budget"]],
        "budget_limits": _budget_limits(g0[gi["budget"]]),
        "dollar_budget": g0[gi["dollar_budget"]],
        "rate_limit": g0[gi["rate_limit"]], "window": g0[gi["window"]],
        "language": g0[gi["language"]],
        "valid_from": g0[gi["valid_from"]], "valid_until": g0[gi["valid_until"]],
    }

    used = {"tokens": 0, "requests": 0, "hours": 0, "dollars": 0.0}
    bi = {f: i for i, f in enumerate(_BU)}
    for cols in _read_tsv_rows(os.path.join(goal_dir, "budget.tsv"), len(_BU)):
        for key in ("tokens", "requests", "hours"):
            try:
                used[key] += int(float(cols[bi["%s_delta" % ("token" if key == "tokens"
                                                             else key)]] or 0))
            except (TypeError, ValueError):
                continue
        try:
            used["dollars"] += float(cols[bi["dollars_delta"]] or 0)
        except (TypeError, ValueError):
            continue

    si = {f: i for i, f in enumerate(_SC)}
    srows = _merged_rows(battle_dir, "scope.tsv")
    superseded = {r[si["amendment_of"]].strip() for r in srows
                  if r[si["amendment_of"]].strip()}
    scope = [{
        "id": r[0], "kind": r[si["kind"]], "matcher": r[si["matcher"]],
        "account": r[si["account"]], "permitted_actions": r[si["permitted_actions"]],
        "amendment_of": r[si["amendment_of"]], "note": r[si["note"]],
        "created": r[si["created"]], "superseded": r[0] in superseded,
    } for r in srows]

    ai = {f: i for i, f in enumerate(_AP)}
    arows = _merged_rows(battle_dir, "approvals.tsv")
    exemptions = [{
        "id": r[ai["id"]], "approver": r[ai["approver"]],
        "timestamp": r[ai["timestamp"]], "note": r[ai["note"]],
    } for r in arows if r[ai["decision"]] == "exempted"]

    history = []
    for no, cols in enumerate(_read_tsv_rows(os.path.join(goal_dir, "timeline.tsv"),
                                             len(_TL)), 1):
        if cols[3].startswith("amend-scope"):
            history.append({"row": no, "ts": cols[0], "event": cols[3]})

    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles, "goal": goal,
        "params": params,
        "budget": {"limits": params["budget_limits"], "used": used,
                   "raw": params["budget"]},
        "scope": scope,
        "counts": {
            "scope_rows": len(scope),
            "scope_heads": sum(1 for r in scope if not r["superseded"]),
            "amendments": sum(1 for r in scope if r["amendment_of"]),
            "exemptions": len(exemptions),
        },
        "exemptions": exemptions,
        "amendment_history": history,
        "p0_over": _p0_over(goal_dir),
        "writable": {
            "action": "amend-scope",
            "kinds": list(_KINDS),
            "requires": ["note"] + (["approval"] if _p0_over(goal_dir) else []),
            "requires_zh": "note=修订必须带因；P0 后另须 approval 指向 approved 行",
            "readonly_note": ("档位与预算三元组随任务声明入账（goals.tsv），"
                              "本页读面展示；范围参数走修订（行+因，入链可审计）。"),
        },
    }


# ------------------------------------------------------------------ 写路径 --

def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _real_runner(argv, env=None):
    """窄门执行器（server._run_cli 同法）：钥不落页面不落盘（env 只进子进程）。"""
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(argv, capture_output=True, text=True, timeout=120, env=e)


def settings_apply(body, ledger_dir=None, runner=None):
    """修订写路径 → (status, payload)。amendment 带因：note 空=422；
    P0 后无 approval=422；窄门 CLI 全量校验（引用闭合/枚举/语法），CLI 拒=422。
    """
    if not isinstance(body, dict):
        return 422, {"ok": False, "error": "请求体须 JSON 对象"}
    action = str(body.get("action") or "")
    if action != "amend-scope":
        return 422, {"ok": False,
                     "error": "未知设置动作: %s（本页只支持 amend-scope 修订——"
                              "档位/预算随任务声明，无静默改写）" % (action or "空")}
    gd = str(ledger_dir or "")
    amendment_of = str(body.get("amendment_of") or "").strip()
    kind = str(body.get("kind") or "").strip()
    matcher = str(body.get("matcher") or "").strip()
    note = str(body.get("note") or "").strip()
    approval = str(body.get("approval") or "").strip()
    if not amendment_of:
        return 422, {"ok": False, "error": "amendment_of 须指向被修订的范围行"}
    if kind not in _KINDS:
        return 422, {"ok": False, "error": "kind 不在四值枚举 %s: %s"
                     % ("/".join(_KINDS), kind or "空")}
    if not matcher:
        return 422, {"ok": False, "error": "matcher 空=拒（范围参数不可为空）"}
    if not note:
        return 422, {"ok": False,
                     "error": "修订必须带因（note 空=拒）——写明理由与批准人"}
    if _p0_over(gd) and not approval:
        return 422, {"ok": False,
                     "error": "P0 后修订须经审批——approval 须指向 approved 行"
                              "（账本级 REJECT 同律）"}
    ts = str(body.get("timestamp") or "").strip() or _utc_now_iso()
    argv = [sys.executable, LEDGER_CLI, "amend-scope", "--goal-dir", gd,
            "--amendment-of=" + amendment_of, "--kind=" + kind,
            "--matcher=" + matcher, "--note=" + note, "--timestamp=" + ts]
    if body.get("account"):
        argv.append("--account=" + str(body["account"]))
    if body.get("permitted_actions"):
        argv.append("--permitted-actions=" + str(body["permitted_actions"]))
    if approval:
        argv.append("--approval=" + approval)
    cp = (runner or _real_runner)(argv)
    out = ((cp.stdout or "") + (cp.stderr or "")).strip()
    first = (cp.stdout or "").splitlines()
    rid = first[0].split("\t")[1] if first and first[0].startswith("OK\t") else ""
    receipt = {"cmd": "amend-scope", "rc": cp.returncode, "id": rid, "out": out[:400]}
    if cp.returncode != 0:
        return 422, {"ok": False, "error": "修订被拒：" + out, "receipt": receipt}
    return 200, {"ok": True, "receipt": receipt}


# ------------------------------------------------------------------ 路由 --

def _settings_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = settings_view(battles_dir=battles_dir, battle=query.get("battle"),
                                ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": "设置参数无效: %s" % e}
    if "error" in payload:
        return 404, payload
    return 200, payload


def _settings_post(body, ledger_dir=None):
    try:
        return settings_apply(body, ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"ok": False, "error": "设置写参数无效: %s" % e}


ROUTES[ROUTE_SETTINGS] = _settings_route
POST_ROUTES[ROUTE_SETTINGS] = _settings_post


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口（GET）→ (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)


def dispatch_post(path, body, ledger_dir=None):
    """include 机制分发口（POST）→ (status, payload) | None(非本域路由)。"""
    fn = POST_ROUTES.get(path)
    if fn is None:
        return None
    return fn(body, ledger_dir=ledger_dir)
