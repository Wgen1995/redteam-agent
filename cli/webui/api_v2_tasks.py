# -*- coding: utf-8 -*-
"""api_v2_tasks（T5·P3+P4）——任务列表/新建任务元信息只读投影，前缀 /api/v2/。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式，禁 datetime.now，
输出确定性——同输入两跑逐字节一致）；挂载=ROUTES 单源表由 include 机制
（api_pages.py，UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_tasks.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。
dispatch(path, query, ledger_dir, battles_dir) 与 api_v2_broadcast 同形。

两路由（全过会话门；无豁免）：
  GET /api/v2/tasks.json
      → 每仗一行聚合（battles 注册表+goals+findings+budget+timeline 单源）：
        名称(goals.target)/目标说明(objective)/状态徽章/预算已用vs帽(80% 预算
        预警线)/发现数(已验证/待验证双色)/开始/更新时间。
  GET /api/v2/new-task-meta.json
      → 新建任务页元信息：battle-kit BRIEF 模板下拉（tests/range/battle-kit/*.md
        只读解析——mission 形八问行提取，缺=诚实空）+枚举表+/api/battle/new
        提交契约+八问清单（页面完备性指示器单源）。

状态机投影（docs/design/task-lifecycle-v1.md 12 态→界面七态子集；宪法#41）：
  DRAFT→草稿  AUTH-PENDING→待授权  ARMED/RUNNING/PAUSED→执行中
  CONVERGED/RETESTING→复测  REPORT-PENDING/SIGN-PENDING→待签发
  SIGNED/CLEANING→已签发  ARCHIVED→已归档；异常终态诚实保留：ABORTED→已中止
  FAILED→环境失败（可见于「全部」）。
推断律（确定性文件分类，零墙钟；先匹配先赢）：
  归档=battle 根 archive-manifest.json 在场（lifecycle 归档 manifest 同义）；
  签发=report/signed/pass.json（api_v2_reports._report_state 同口径本地单源）；
  待签发=report 渲染工件在场（report/draft/*.md 或 findings.json/sarif）；
  已中止=runner tsv 末次 DONE final_rc≠0；
  执行中=registry.json 活 pid（os.kill 探测——死尸回收同判据）或 runner 已
  点火未完跑；复测=timeline 有 replay 行（replay-probe/replay:EV 两形）；
  待点火=八问全真（goals 行+scope include 行）；待授权=八问缺件；草稿=无 goals 行。
"""
import json
import os
import re

from ledger import core
from ledger.session_view import default_battles_dir, list_battles

ROUTE_TASKS = "/api/v2/tasks.json"
ROUTE_NEW_META = "/api/v2/new-task-meta.json"
ROUTES = {ROUTE_TASKS: None, ROUTE_NEW_META: None}   # 尾部赋真身（前向引用）

_WARN_PCT = 80.0                    # 预算预警线（宪法#41 人话词：琥珀线→预警线）
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REPLAY_RE = re.compile(r"(?:^|\s)(?:replay-probe \S+ verdict=|replay:(?:EV|FD)-[^:\s]+:)")
_DONE_RC_RE = re.compile(r"final_rc=(-?\d+)")
_RUNNER_TSV = "opencode-run.log.runner.tsv"
_MODEL_TIERS = ("strong", "weak")
_GUARD_TIERS = ("T1", "T2", "T3")
ARCHIVE_MANIFEST = "archive-manifest.json"

# 界面七态词表（筛选/徽章单源；「全部」居首）
STATE_FILTERS = ("全部", "草稿", "待授权", "执行中", "复测", "待签发", "已签发", "已归档")


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _gen_key(name):
    """G-* 代目录自然序键（server._latest_gen/api_v2_reports 同律：G-r9<G-r43）。"""
    digits = [int(d) for d in re.findall(r"\d+", name)]
    return (digits or [0])[0]


def _gen_dirs(battle_dir):
    """战目录 G-* 代目录自然序列表；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []
    return sorted(names, key=_gen_key)


def _to_num(s):
    """tsv 数串→float（空/坏=0.0——预算行缺段不炸）。"""
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return 0.0


def _cap_num(seg):
    """帽段解析：'2M'/'50000'/'40' → 数（K/M/G 后缀；空=0）。"""
    s = str(seg or "").strip()
    if not s:
        return 0.0
    m = re.match(r"^([0-9.]+)\s*([KkMmGg]?)$", s)
    if not m:
        return _to_num(s)
    scale = {"": 1.0, "k": 1e3, "m": 1e6, "g": 1e9}[m.group(2).lower()]
    return float(m.group(1)) * scale


def _pid_alive(pid):
    """OS 事实：pid 活性（battle_registry._default_pid_alive 同判据）。"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def _registry_live(root):
    """registry.json → {battle_n: 活}（死尸回收=不活；坏册=空——不执法不炸页）。"""
    p = os.path.join(root, "registry.json")
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        entries = doc.get("entries") or {}
    except (OSError, ValueError, AttributeError):
        return {}
    out = {}
    for key, ent in entries.items():
        try:
            n = int(str(key))
        except ValueError:
            continue
        pid = (ent or {}).get("pid") if isinstance(ent, dict) else None
        out[n] = _pid_alive(pid)
    return out


def _tsv_rows(path, tname):
    """tsv 文本→列行（core.Session 同形但零锁零缓存——列表页逐战一次读）。"""
    text = _read_text(path)
    if not text:
        return []
    width = len(core.TABLES[tname])
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cols = [core.unesc(c) for c in line.split("\t")]   # Session.rows 同反escape
        out.append(cols + [""] * (width - len(cols)))
    return out


def _cell(tname, r, col):
    return r[core.TABLES[tname].index(col)]


def _latest_by_id(rows_iter, tname):
    """多代合并律（api_v2_retest 同口径）：同 id 后代胜，保首现序。"""
    out, order = {}, []
    for r in rows_iter:
        k = r[0].strip()
        if not k:
            continue
        if k not in out:
            order.append(k)
        out[k] = r
    return out, order


def _last_done_rc(battle_dir):
    """runner tsv 末次 DONE final_rc（无 DONE=None——未完跑）。"""
    lines = [l for l in _read_text(
        os.path.join(battle_dir, _RUNNER_TSV)).splitlines() if l.strip()]
    for line in reversed(lines):
        cols = line.split("\t")
        if len(cols) >= 2 and cols[1].strip() == "DONE":
            m = _DONE_RC_RE.search(cols[2] if len(cols) > 2 else "")
            return int(m.group(1)) if m else 0
    return None


def _has_replay(rows_tl):
    return any(_REPLAY_RE.search(r[3]) for r in rows_tl if len(r) > 3)


def _has_render(gen_dir):
    if any(n.endswith(".md") for n in _ls(os.path.join(gen_dir, "report", "draft"))):
        return True
    return any(os.path.isfile(os.path.join(gen_dir, "report", n))
               for n in ("findings.json", "findings.sarif"))


def _ls(path):
    try:
        return sorted(os.listdir(path))
    except OSError:
        return []


def _signed(gen_dir):
    return os.path.isfile(os.path.join(gen_dir, "report", "signed", "pass.json"))


# ------------------------------------------------------- 状态机投影（单源） --

def _eight_missing(goal, scope_include):
    """goals 行+范围 → 八问缺件中文清单（AUTH-PENDING detail 用；全过=[]）。
    与 server._auth_eight_questions 同域（表单域在册版）：①授权件四件 ②窗口期
    ③范围 ④联系人 ⑤预算 ⑥凭据来源(business_context 前缀) ⑦强度档 ⑧(表单勾选
    在提交侧，立项后恒真)——这里只验立项账本能自证的件。"""
    missing = []
    if not (goal.get("auth_doc") and goal.get("auth_sha256")
            and _HEX64_RE.match(goal.get("auth_sha256") or "")
            and goal.get("signer")):
        missing.append("①授权书")
    vf, vu = goal.get("valid_from") or "", goal.get("valid_until") or ""
    if not (_ISO_Z_RE.match(vf or "") and _ISO_Z_RE.match(vu or "")):
        missing.append("②授权窗口期")
    if not scope_include:
        missing.append("③范围白名单")
    if not (goal.get("emergency_contact") or "").strip():
        missing.append("④紧急联系人")
    if not (goal.get("budget") or "").strip():
        missing.append("⑤预算硬顶")
    if "凭据" not in (goal.get("business_context") or ""):
        missing.append("⑥凭据来源")
    if goal.get("model_tier") not in _MODEL_TIERS \
            or goal.get("guard_tier") not in _GUARD_TIERS:
        missing.append("⑦强度档")
    return missing


def _battle_state(battle_dir, gen_dir, goal, scope_include, live, tl, has_findings):
    """→ {code,label,detail}（12 态→界面子集；先匹配先赢，零墙钟）。

    顺位律（实勘教训：boot 脚本立的仗先于表单期字段存在——执行在案的事实
    [runner/发现/重放/报告] 压过 goals 行表单域完备，缺件只拦未执行的仗）。"""
    if goal is None:
        return {"code": "DRAFT", "label": "草稿", "detail": "未立项（无 goals 行）"}
    if os.path.isfile(os.path.join(battle_dir, ARCHIVE_MANIFEST)):
        return {"code": "ARCHIVED", "label": "已归档", "detail": "归档清单在场（冷存储）"}
    if gen_dir is not None and _signed(gen_dir):
        return {"code": "SIGNED", "label": "已签发", "detail": "签发凭证在场（锁定）"}
    if gen_dir is not None and _has_render(gen_dir):
        return {"code": "SIGN-PENDING", "label": "待签发",
                "detail": "报告已渲染 · 待双人签发"}
    rc = _last_done_rc(battle_dir)
    if rc is not None and rc != 0:
        return {"code": "ABORTED", "label": "已中止",
                "detail": "执行中止（runner 退出码 %d）" % rc}
    if live:
        return {"code": "RUNNING", "label": "执行中", "detail": "在册执行（注册表活 pid）"}
    if rc is None and _runner_started(battle_dir):
        return {"code": "RUNNING", "label": "执行中", "detail": "已点火（runner 未完跑）"}
    exec_evidence = (rc == 0) or has_findings or _has_replay(tl)
    if exec_evidence:
        if _has_replay(tl):
            return {"code": "RETESTING", "label": "复测",
                    "detail": "验证环在跑（timeline 有重放行）"}
        return {"code": "CONVERGED", "label": "复测",
                "detail": "执行完跑 · 待复测"}
    missing = _eight_missing(goal, scope_include)
    if missing:
        return {"code": "AUTH-PENDING", "label": "待授权",
                "detail": "八问缺 %d 项：%s" % (len(missing), "、".join(missing))}
    return {"code": "ARMED", "label": "执行中", "detail": "已授权 · 待点火"}


def _runner_started(battle_dir):
    text = _read_text(os.path.join(battle_dir, _RUNNER_TSV))
    return any(len(l.split("\t")) >= 2 and l.split("\t")[1].strip() == "LAUNCH"
               for l in text.splitlines() if l.strip())


def _merged_tl(battle_dir):
    """timeline 多代合并（代自然序+文件序——broadcast._timeline_rows 同律）。"""
    rows = []
    for gen in _gen_dirs(battle_dir):
        rows.extend(_tsv_rows(os.path.join(battle_dir, gen, "timeline.tsv"),
                              "timeline.tsv"))
    return rows


# ------------------------------------------------- ①b 新建任务元信息投影 --

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_KIT_DIR = os.path.join(_REPO_ROOT, "tests", "range", "battle-kit")

_OBJ_RE = re.compile(r"^\s*(?:\d+\)\s*)?目标[：:]\s*(.+)$", re.M)
_SCOPE_RE = re.compile(r"(?:^|\s|；|;)(?:\d+\)\s*)?范围[：:]\s*(.+)$", re.M)
_BUDGET_RE = re.compile(r"(?:^|\s)(?:\d+\)\s*)?预算[：:]\s*([0-9KMkmG.]+(?:;[0-9KMkmG.]*)*)")
_TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)


def _kit_templates(kit_dir):
    """battle-kit BRIEF 模板下拉（*.md 只读解析；py/说明件不入——BRIEF=md 件）。

    mission 形结构行提取（battle-kit/历史 mission.txt 同形）：目标/范围
    include 段/预算三段；纯 prose 模板缺行=诚实空（不虚构模板值）。
    """
    try:
        names = sorted(n for n in os.listdir(kit_dir)
                       if n.startswith("BRIEF") and n.endswith(".md"))
    except OSError:
        return []
    out = []
    for n in names:
        path = os.path.join(kit_dir, n)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        objective = ""
        m = _OBJ_RE.search(text)
        if m:
            objective = m.group(1).strip()
        scope_lines = []
        m = _SCOPE_RE.search(text)
        if m:
            seg = m.group(1)
            inc = re.search(r"include=([^；;]+)", seg)
            if inc:
                for part in re.split(r"\s*与\s*|\s+", inc.group(1).strip()):
                    part = part.strip().rstrip("。，,")
                    if part:
                        scope_lines.append(part)
        budget = ""
        m = _BUDGET_RE.search(text)
        if m:
            budget = m.group(1).strip().rstrip("。")
        title = ""
        m = _TITLE_RE.search(text)
        if m:
            title = m.group(1).strip()
        out.append({"id": n[:-3], "name": title or n[:-3], "file":
                    "tests/range/battle-kit/" + n, "objective": objective,
                    "scope_lines": scope_lines, "budget": budget})
    return out


_EIGHT = (
    {"no": "①", "key": "auth_doc", "label": "授权书原件",
     "hint": "PDF/PNG 拖拽上传，浏览器实算 sha256，原件字节随表单上送"},
    {"no": "②", "key": "window", "label": "授权窗口期", "hint": "起止时刻（UTC），止须晚于起"},
    {"no": "③", "key": "legal", "label": "法律确认", "hint": "勾选确认本次测试经真实授权"},
    {"no": "④", "key": "scope", "label": "范围白名单", "hint": "每行一条：域名后缀或网段，缺范围不开测"},
    {"no": "⑤", "key": "cred_source", "label": "凭据来源", "hint": "测试账号从哪来"},
    {"no": "⑥", "key": "budget", "label": "预算硬顶", "hint": "token / 请求次数 / 时长 三段"},
    {"no": "⑦", "key": "tier", "label": "强度档", "hint": "执行档与拦截档"},
    {"no": "⑧", "key": "contact", "label": "紧急联系人", "hint": "授权方 7×24 可达通道"},
)


def new_task_meta_view(kit_dir=None):
    """新建任务页元信息 → {templates, enums, submit, eight}（只读确定性）。

    枚举/提交契约与 server._auth_eight_questions 同域单源（本投影只描述，
    校验仍在服务端——缺一=422 字段级拒因回显）。
    """
    root = kit_dir if kit_dir else DEFAULT_KIT_DIR
    return {
        "templates": _kit_templates(root),
        "enums": {"model_tier": list(_MODEL_TIERS), "guard_tier": list(_GUARD_TIERS),
                  "cred_source": ["客户提供", "自备（自行注册）", "盲测（无凭据探测）"]},
        "submit": {"endpoint": "/api/battle/new", "method": "POST",
                   "requires": ["name", "note", "budget", "scope",
                                "auth", "cred_source", "emergency_contact",
                                "model_tier", "guard_tier", "legal_ack"],
                   "note": "授权八问缺一=422（字段级拒因回显）；成功=建任务并留痕"},
        "eight": [dict(q) for q in _EIGHT],
    }


def new_task_meta_route(query, ledger_dir=None, battles_dir=None, kit_dir=None):
    """路由适配层 → (200, payload)；元信息无 4xx 面（kit 缺=空模板诚实态）。"""
    return 200, new_task_meta_view(kit_dir=kit_dir)


# ---------------------------------------------------------------- ① 列表投影 --

def tasks_view(battles_dir=None):
    """每仗一行聚合 → {battles, counts, states}（战号升序；只读确定性）。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    live_map = _registry_live(root)
    battles = []
    for b in list_battles(root):
        battle_dir = os.path.join(root, b["id"])
        gens = _gen_dirs(battle_dir)
        gen_dir = os.path.join(battle_dir, gens[-1]) if gens else None

        goal = None
        if gen_dir is not None:
            grows = _tsv_rows(os.path.join(gen_dir, "goals.tsv"), "goals.tsv")
            if grows:
                goal = {k: _cell("goals.tsv", grows[-1], k)
                        for k in core.TABLES["goals.tsv"]}

        scope_include = False
        frows = []
        for gen in gens:
            for r in _tsv_rows(os.path.join(battle_dir, gen, "scope.tsv"),
                               "scope.tsv"):
                if _cell("scope.tsv", r, "kind") == "include":
                    scope_include = True
                frows.append(r)

        tl = _merged_tl(battle_dir)
        # 发现：多代合并同 id 后代胜 → active 三色计数（宪法#41 验证状态词）。
        latest, order = _latest_by_id(
            (r for gen in gens for r in _tsv_rows(
                os.path.join(battle_dir, gen, "findings.tsv"), "findings.tsv")),
            "findings.tsv")
        findings = {"total": 0, "verified": 0, "pending": 0, "ruled_out": 0}
        for k in order:
            r = latest[k]
            if _cell("findings.tsv", r, "status") != "active":
                continue
            findings["total"] += 1
            expl = _cell("findings.tsv", r, "exploitation_status")
            if expl == "verified":
                findings["verified"] += 1
            elif expl == "ruled_out":
                findings["ruled_out"] += 1
            else:
                findings["pending"] += 1

        state = _battle_state(battle_dir, gen_dir, goal, scope_include,
                              live_map.get(b["n"], False), tl,
                              findings["total"] > 0)

        # 预算：帽=goals.budget 三段（token;requests;hours；K/M/G 后缀），
        # 已用=各代 budget.tsv 增量累计（网关侧计量口径随行披露）。
        segs = (goal or {}).get("budget") or ""
        parts = segs.split(";")
        used = {"token": 0.0, "requests": 0.0, "hours": 0.0}
        for gen in gens:
            for r in _tsv_rows(os.path.join(battle_dir, gen, "budget.tsv"),
                               "budget.tsv"):
                used["token"] += _to_num(_cell("budget.tsv", r, "token_delta"))
                used["requests"] += _to_num(_cell("budget.tsv", r, "requests_delta"))
                used["hours"] += _to_num(_cell("budget.tsv", r, "hours_delta"))
        budget = {"raw": segs}
        for key, idx in (("token", 0), ("requests", 1), ("hours", 2)):
            cap = _cap_num(parts[idx]) if idx < len(parts) else 0.0
            pct = round(used[key] / cap * 100.0, 1) if cap > 0 else 0.0
            budget[key] = {
                "used": int(used[key]) if used[key] == int(used[key]) else used[key],
                "cap": int(cap) if cap == int(cap) else cap,
                "pct": pct,
                "warn": pct >= _WARN_PCT, "over": cap > 0 and used[key] > cap}

        created = (goal or {}).get("created") or (tl[0][0] if tl else "")
        updated = tl[-1][0] if tl else created

        battles.append({
            "battle": b["id"], "n": b["n"],
            "goal": gens[-1] if gens else "",
            "goal_id": (goal or {}).get("id", ""),
            "name": (goal or {}).get("target", ""),
            "objective": (goal or {}).get("objective", ""),
            "state": state, "budget": budget, "findings": findings,
            "created": created, "updated": updated,
        })

    by_label = {}
    for b in battles:
        by_label[b["state"]["label"]] = by_label.get(b["state"]["label"], 0) + 1
    return {"battles": battles,
            "counts": {"battles": len(battles), "by_label": by_label},
            "states": [{"label": s} for s in STATE_FILTERS],
            "budget_warn_pct": _WARN_PCT}


def tasks_route(query, ledger_dir=None, battles_dir=None):
    """路由适配层 → (200, payload)；列表无 4xx 面（空根=空列表诚实态）。"""
    return 200, tasks_view(battles_dir=battles_dir if battles_dir else None)


ROUTES[ROUTE_TASKS] = tasks_route
ROUTES[ROUTE_NEW_META] = new_task_meta_route


def dispatch(path, query, ledger_dir=None, battles_dir=None, kit_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。

    UI-1 挂法（tests/test_webui_pagespec_tasks.py / _new_task.py
    _V2MountHandler 钉）:
        dispatch(path, query, server.ledger_dir, battles_dir=server.battles_dir,
                 kit_dir=getattr(server, "kit_dir", None))
    """
    fn = ROUTES.get(path)
    if fn is None:
        return None
    if path == ROUTE_NEW_META:
        return fn(query, kit_dir=kit_dir)
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
