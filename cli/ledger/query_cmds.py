# -*- coding: utf-8 -*-
"""tanyin ledger 查询命令（批次 1 T7）——契约：contracts/02a §2（第 19-28 节）+ 终审补全。

清单=契约 02 查询类 12 条去掉 set-cred-status（终审归写入）与 next-id（core 内建），
redact-scan 在 special.py（专用六条之一，双入口 cli/tanyin-redact）。
只读纪律：输出=过滤行流（首行 #count=N＋TSV 投影，排序确定，禁全量回灌）；
退出码 0=成功 1=门禁失败 2=用法/环境错误。参数本批仅 --key=value／旗标
（值经临时文件/stdin 的场景留待批次 2，TODO）。
【推导】标注=02a 已终审冻结的起草语义，非本文件发明。
"""
import ipaddress, json, sys

from . import core
from .schemas import TABLES

TAB = chr(9)
DEFAULT_TOP = 20  # 【推导】摘要化默认 top-N；--top=0 = 全量


class UsageError(Exception):
    """用法错误 → 退出码 2。"""


def usage_guard(fn):
    """包装 HANDLERS 导出函数：UsageError → stderr 用法提示＋退出码 2
    （tanyin-ledger 入口把一般异常归 1，用法错须在此拦截）。"""
    def wrapped(goal_dir, rest):
        try:
            return fn(goal_dir, rest)
        except UsageError as e:
            sys.stderr.write("用法错误: %s\n" % e)
            return 2
    return wrapped


def parse_kv(rest):
    """--key=value / --flag；位置参数（不以 -- 开头）单列返回。"""
    args, pos = {}, []
    for tok in rest:
        if not tok.startswith("--"):
            pos.append(tok)
            continue
        body = tok[2:]
        if "=" in body:
            k, v = body.split("=", 1)
            args[k] = v
        else:
            args[body] = True
    return args, pos


def _idx(t, f):
    return TABLES[t].index(f)


def _cell(row, t, f):
    return row[_idx(t, f)]


def latest_by(rows, t, key_fields):
    """事件溯源：同键多行取最新（文件序后者覆盖前者，§4.1「取最新」是账本命令）。"""
    out = {}
    for r in rows:
        out[tuple(r[_idx(t, k)] for k in key_fields)] = r
    return out


def latest_intents(s):
    return latest_by(s.rows("intents.tsv"), "intents.tsv", ["id"])


def latest_matrix(s):
    return latest_by(s.rows("matrix.tsv"), "matrix.tsv", ["attack_surface", "vuln_class"])


def derived_from_sources(s):
    """derived_from 出边（fact→intent）的 fact 集合——「未消费 fact」定义（§4.8）。"""
    return {r[_idx("edges.tsv", "source_id")]
            for r in s.rows("edges.tsv")
            if r[_idx("edges.tsv", "kind")] == "derived_from"}


def unconsumed_facts(s):
    used = derived_from_sources(s)
    out = [r for r in s.rows("facts.tsv")
           if r[_idx("facts.tsv", "id")] not in used]
    out.sort(key=lambda r: r[0])
    return out


def blocked_intents(s):
    return sorted((r for r in latest_intents(s).values()
                   if r[_idx("intents.tsv", "status")] == "blocked"),
                  key=lambda r: r[0])


def matrix_gap_cells(s):
    """空格（state 空=未检查）清单——主矩阵+子矩阵（submatrix:/authz-diff: 前缀行）全量行键。"""
    gaps = [r for _, r in sorted(latest_matrix(s).items())
            if r[_idx("matrix.tsv", "state")].strip() == ""]
    return gaps


# ---------------------------------------------------------------- 预算树（§4.10）

_MULT = {"k": 10 ** 3, "m": 10 ** 6, "g": 10 ** 9}


def parse_num(tok):
    """'2M'→2000000（契约 01 §3.1 budget 示例 2M;50000;40）；整数/小数原样。"""
    t = str(tok).strip()
    if t and t[-1].lower() in _MULT:
        return float(t[:-1]) * _MULT[t[-1].lower()]
    return float(t)


def _round6(x):
    return round(x + 0.0, 6)


def budget_tree(s):
    """goals 三元组（根）+intents.budget_share（叶）+budget.tsv 流水上卷 → 树形余量。

    返回 dict：{"goal": {...}|None, "intents": [...]}。
    share 解析【推导】：';' 三/四段=绝对值；单值小数=根预算份额（夹具形态）。
    """
    grows = s.rows("goals.tsv")
    root = None
    if grows:
        parts = (_cell(grows[0], "goals.tsv", "budget").split(";") + ["", "", ""])[:3]
        tok, req, hrs = (parse_num(p) if p.strip() else 0.0 for p in parts)
        dollars = _cell(grows[0], "goals.tsv", "dollar_budget")
        dollars = parse_num(dollars) if dollars.strip() else None
        root = {"token": tok, "requests": req, "hours": hrs, "dollars": dollars}

    intent_used = {}
    goal_direct = {"token": 0.0, "requests": 0.0, "hours": 0.0, "dollars": 0.0}
    for r in s.rows("budget.tsv"):
        scope = _cell(r, "budget.tsv", "scope")
        d = {"token": parse_num(_cell(r, "budget.tsv", "token_delta") or 0),
             "requests": parse_num(_cell(r, "budget.tsv", "requests_delta") or 0),
             "hours": parse_num(_cell(r, "budget.tsv", "hours_delta") or 0),
             "dollars": parse_num(_cell(r, "budget.tsv", "dollars_delta") or 0)}
        if scope.startswith("INT-"):
            cur = intent_used.setdefault(scope, {"token": 0.0, "requests": 0.0,
                                                 "hours": 0.0, "dollars": 0.0})
            for k in cur:
                cur[k] += d[k]
        else:  # scope=goal（字面量=目标级总预算，契约 01 终审裁决）
            for k in goal_direct:
                goal_direct[k] += d[k]

    intents = []
    for key, r in sorted(latest_intents(s).items()):
        iid = key[0]  # latest_intents 键为元组 ("INT-…",)
        share_raw = _cell(r, "intents.tsv", "budget_share")
        if ";" in share_raw:
            parts = (share_raw.split(";") + ["", "", ""])[:4]
            share = {"token": parse_num(parts[0]) if parts[0].strip() else 0.0,
                     "requests": parse_num(parts[1]) if parts[1].strip() else 0.0,
                     "hours": parse_num(parts[2]) if parts[2].strip() else 0.0,
                     "dollars": parse_num(parts[3]) if parts[3].strip() else 0.0}
        else:
            frac = parse_num(share_raw) if share_raw.strip() else 0.0
            share = None
            if root:
                share = {"token": frac * root["token"],
                         "requests": frac * root["requests"],
                         "hours": frac * root["hours"],
                         "dollars": frac * root["dollars"] if root["dollars"] is not None else None}
        used = intent_used.get(iid, {"token": 0.0, "requests": 0.0,
                                     "hours": 0.0, "dollars": 0.0})
        intents.append({"id": iid, "share": share, "used": used})

    goal = None
    if root:
        used = {k: goal_direct[k] + sum(i["used"][k] for i in intents)
                for k in goal_direct}
        goal = {"budget": _cell(grows[0], "goals.tsv", "budget"),
                "limit": root, "used": used}
    return {"goal": goal, "intents": intents}


def budget_exhausted(s):
    """预算树穿：goal 根任一维度 used>limit，或任一 intent used>share（§4.10 树形）。"""
    t = budget_tree(s)
    goal = t["goal"]
    if goal:
        for k, limit in goal["limit"].items():
            if limit is None:
                continue
            if goal["used"][k] > limit:
                return True
    for i in t["intents"]:
        if i["share"] is None:
            continue
        for k, limit in i["share"].items():
            if limit is None:
                continue
            if i["used"][k] > limit:
                return True
    return False


def converge_state(s):
    """收敛判定（终审补全 1，定稿 §5.4）：空格清零（主+子矩阵）/预算树未穿/
    无 unconsumed fact/无 blocked intent。预算穿=合法终态 budget-exhausted（P4 降级流）。"""
    if budget_exhausted(s):
        return "budget-exhausted"
    ok = (not matrix_gap_cells(s) and not unconsumed_facts(s)
          and not blocked_intents(s))
    return "converged" if ok else "running"  # 【推导】中间态输出 running（契约仅载两终态）


# ---------------------------------------------------------------- scope 判定（§4.4）

def _cidr_hit(matcher, value):
    try:
        net = ipaddress.ip_network(matcher, strict=False)
        addr = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    try:
        return addr in net
    except TypeError:
        return False


def _domain_hit(matcher, value):
    m = matcher.lstrip("*").lstrip(".")
    v = value.strip().lower()
    return v == m or v.endswith("." + m)


def judge_scope(s, value):
    """CIDR/域名后缀/通配机械匹配（非 LLM，§4.4）；exclude 优先，无 include 命中=界外。"""
    inc = exc = False
    for r in s.rows("scope.tsv"):
        kind, matcher = _cell(r, "scope.tsv", "kind"), _cell(r, "scope.tsv", "matcher")
        if kind not in ("include", "exclude") or not matcher:
            continue
        hit = _cidr_hit(matcher, value) if "/" in matcher else _domain_hit(matcher, value)
        if kind == "include":
            inc = inc or hit
        else:
            exc = exc or hit
    return "in_scope" if (inc and not exc) else "out_of_scope"


def in_scope_assets(s):
    """in_scope 资产行（in_scope 列非空且非否定标记——夹具用 1/0，定稿用枚举，兼容两者）。"""
    out = []
    for r in s.rows("assets.tsv"):
        v = _cell(r, "assets.tsv", "in_scope").strip().lower()
        if v not in ("", "0", "false", "out_of_scope"):
            out.append(r)
    return out


# ---------------------------------------------------------------- 命令实现

def _top(args):
    if "top" not in args:
        return DEFAULT_TOP
    try:
        n = int(args["top"])
    except (TypeError, ValueError):
        raise UsageError("--top 需整数")
    if n < 0:
        raise UsageError("--top 需非负整数")
    return n


def _stream(count, rows, top):
    print("#count=%d" % count)
    for r in rows[:top] if top else rows:
        print(TAB.join(r))


def h_unconsumed_facts(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos:
        raise UsageError("unconsumed-facts 无位置参数")
    s = core.Session(goal_dir)
    rows = [[_cell(r, "facts.tsv", f) for f in ("id", "kind", "target", "confidence")]
            for r in unconsumed_facts(s)]
    _stream(len(rows), rows, _top(args))
    return 0


def h_pending_intents(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos:
        raise UsageError("pending-intents 无位置参数")
    s = core.Session(goal_dir)
    rows = [[_cell(r, "intents.tsv", f)
             for f in ("id", "title", "kind", "engine", "budget_share")]
            for r in sorted(latest_intents(s).values(), key=lambda r: r[0])
            if _cell(r, "intents.tsv", "status") == "pending"]
    _stream(len(rows), rows, _top(args))
    return 0


def h_matrix_gaps(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos:
        raise UsageError("matrix-gaps 无位置参数")
    s = core.Session(goal_dir)
    if args.get("baseline"):
        latest = latest_matrix(s)
        surfaces = {k[0] for k in latest}
        assets = in_scope_assets(s)
        asset_vals = {_cell(r, "assets.tsv", "value") for r in assets}
        # 【推导】覆盖判定：in_scope 资产值 ⊆ 矩阵攻击面（matrix-init 行键源自 assets.value）
        covered = "true" if asset_vals and asset_vals <= surfaces else "false"
        print("#baseline_rows=%d%s#in_scope_surfaces=%d%scovered=%s"
              % (len(latest), TAB, len(assets), TAB, covered))
        return 0
    rows = [[_cell(r, "matrix.tsv", f) for f in ("attack_surface", "vuln_class")]
            for r in matrix_gap_cells(s)]
    _stream(len(rows), rows, _top(args))
    return 0


def h_converge_check(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("converge-check 无参数")
    print(converge_state(core.Session(goal_dir)))
    return 0


def h_intent_status(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or "id" not in args:
        raise UsageError("intent-status 需 --id=<intents.id>")
    s = core.Session(goal_dir)
    r = latest_intents(s).get((args["id"],))
    if r is None:
        print("#count=0")  # 【推导】无此行口径对照 02a 第 24 节
        return 0
    print(TAB.join(_cell(r, "intents.tsv", f) for f in ("id", "status", "reason")))
    return 0


def h_matrix_get(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or "attack-surface" not in args or "vuln-class" not in args:
        raise UsageError("matrix-get 需 --attack-surface=<面> --vuln-class=<类>")
    s = core.Session(goal_dir)
    r = latest_matrix(s).get((args["attack-surface"], args["vuln-class"]))
    if r is None:
        print("#count=0")  # 【推导】未置格/不存在键：空格查询矩阵里无行即无格
        return 0
    print(TAB.join(_cell(r, "matrix.tsv", f)
                   for f in ("attack_surface", "vuln_class", "state", "reason",
                             "intent_id", "updated")))
    return 0


def h_scope_check(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos:
        raise UsageError("scope-check 无位置参数")
    s = core.Session(goal_dir)
    if args.get("all-assets"):
        if len(args) != 1:
            raise UsageError("--all-assets 不与其他参数并用")
        assets = sorted(s.rows("assets.tsv"), key=lambda r: r[0])
        unresolved = [r for r in assets
                      if not _cell(r, "assets.tsv", "in_scope").strip()]
        print("#judged=%d/%d" % (len(assets) - len(unresolved), len(assets)))
        for r in unresolved[:DEFAULT_TOP]:
            print(TAB.join([_cell(r, "assets.tsv", "id"), _cell(r, "assets.tsv", "value")]))
        return 0
    if "type" in args and "value" in args:
        print(judge_scope(s, args["value"]))
        return 0
    raise UsageError("scope-check 需 --all-assets 或 --type=<t> --value=<v>")


def h_budget_check(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("budget-check 无参数")

    def proj(d):
        if d is None:
            return None
        out = {}
        for k in ("token", "requests", "hours", "dollars"):
            v = d.get(k)
            if v is None:
                continue
            out[k] = int(v) if k in ("token", "requests") and float(v).is_integer() else _round6(v)
        return out

    t = budget_tree(core.Session(goal_dir))
    goal = None
    if t["goal"]:
        limit = proj(t["goal"]["limit"])
        used = proj(t["goal"]["used"])
        left = ({k: _round6(limit[k] - used[k]) for k in limit} if limit and used else None)
        goal = {"budget": t["goal"]["budget"], "limit": limit, "used": used, "left": left}
    intents = []
    for i in t["intents"]:
        share, used = proj(i["share"]), proj(i["used"])
        left = ({k: _round6(share[k] - used[k]) for k in share} if share and used else None)
        intents.append({"id": i["id"], "share": share, "used": used, "left": left})
    print(json.dumps({"goal": goal, "intents": intents},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


def _replay_status(s):
    """外部副作用清单核销状态【推导】：reverted=后续 timeline 事件 revert:<原事件>；
    exempted=approvals 行 decision=exempted 且 note 含原事件文本（P6.0 残留豁免落 approvals）。"""
    tl = s.rows("timeline.tsv")
    ev_idx, rc_idx = _idx("timeline.tsv", "event"), _idx("timeline.tsv", "revert_cmd")
    approvals = s.rows("approvals.tsv")
    items = []
    for i, r in enumerate(tl):
        if not r[rc_idx].strip():
            continue  # 纯账本状态行 revert_cmd 为空，不列（§0.3 口径 4）
        ev = r[ev_idx]
        reverted = any(x[ev_idx] == "revert:" + ev for x in tl[i + 1:])
        exempted = any(_cell(a, "approvals.tsv", "decision") == "exempted"
                       and ev in _cell(a, "approvals.tsv", "note") for a in approvals)
        status = "reverted" if reverted else ("exempted" if exempted else "pending")
        items.append({"row": r, "status": status})
    return items


def h_cleanup_checklist(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"verify"}:
        raise UsageError("cleanup-checklist [--verify]")
    s = core.Session(goal_dir)
    items = _replay_status(s)
    if not args.get("verify"):
        print("#items=%d" % len(items))
        for it in items[:DEFAULT_TOP]:
            r = it["row"]
            print(TAB.join([_cell(r, "timeline.tsv", f)
                            for f in ("timestamp", "event", "revert_cmd")]
                           + [it["status"]]))
        return 0
    pending = [it for it in items if it["status"] == "pending"]
    if not pending:
        any_exempt = any(it["status"] == "exempted" for it in items)
        print("exemptions_complete" if any_exempt else "all_reverted")
        return 0
    print("FAIL" + TAB + "未核销行=%d" % len(pending))
    for it in pending[:DEFAULT_TOP]:
        r = it["row"]
        print(TAB.join([_cell(r, "timeline.tsv", f)
                        for f in ("timestamp", "event", "revert_cmd")]))
    return 1


HANDLERS = {name: usage_guard(fn) for name, fn in {
    "unconsumed-facts": h_unconsumed_facts,
    "pending-intents": h_pending_intents,
    "matrix-gaps": h_matrix_gaps,
    "converge-check": h_converge_check,
    "intent-status": h_intent_status,
    "matrix-get": h_matrix_get,
    "scope-check": h_scope_check,
    "budget-check": h_budget_check,
    "cleanup-checklist": h_cleanup_checklist,
}.items()}
