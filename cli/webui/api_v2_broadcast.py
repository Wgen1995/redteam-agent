# -*- coding: utf-8 -*-
"""webui api_v2 broadcast（UI-2·P5.3 播报页签）——timeline 播报类行只读投影。

契约（docs/design/ui-spec-complete-v1.md P5.3 + battle-cockpit-v1.md 页签3）:
  路由: GET /api/v2/broadcast.json?battle=N&frame=M&tail=K
        （/api/v2/ 前缀;路由注册与登录门由共享壳 server 侧统一接线——本模块
        纯投影零 HTTP,与 _PAGE_API 表项同形: 调用方传参,返回 JSON 可序列化 dict）
  battle: None=最新战（战号最大）;"N"/int/"battle-N" 归一;不存在 → {"error":...,
        "battles":[...]};坏战号 → ValueError（路由层转 404/422,session_api 先例）。
  frame:  演变回放帧=timeline 行号;只显示该帧前（行号 < frame）;坏值 → ValueError。
  tail:   只取最近 N 条播报（默认 200;页面首屏有界,直播增量走 SSE）。

播报类行定义（零新增状态,全账本真投影）:
  - 智能体叙述（kind=agent）  = 战士写账行（actor="CLI"——智能体每步落账即播报）;
  - 操作员气泡（kind=operator）= battle-say 行（对话介入并入=人在环,POST
    /api/battle/say 留痕;账本只记长度,正文经指令通道下发,页面侧以行号回执补显）;
  - 平台执法行（总控/canary/egress）与验证环行（replay）不入播报流（P5.3 双气泡律）。

人话律（ui-copy-standard-v1.md 宪法 #41）: 已知动词译人话（text 字段）,原始
event 全文随行携带（mono 小字回显,账本锚定是本页立身之本）;内部代号不上屏
指文案,text 永不裸出动词。

证据跳转: 播报行提取 EV-\\S+ 引用,联 E-index.tsv 解析挂接发现 → 页面 hover
「查看证据」跳 /evidence#f=<发现号>（evidence 页既有锚,单源不另造）。

只读律: 一切文件 r 模式 open,零写入零子进程;禁 datetime.now（输出确定性:
行序/翻译全取文件序）。
"""
import os
import re

from ledger import core
from ledger.session_view import default_battles_dir, list_battles

DEFAULT_TAIL = 200
AGENT_ACTOR = "CLI"                     # 战士写账=智能体叙述（session_view 词表同源）
OPERATOR_VERB = "battle-say"            # POST /api/battle/say 留痕行
_BATTLE_DIR = re.compile(r"^battle-(\d+)$")
_EV_REF = re.compile(r"EV-[A-Za-z0-9_.-]+")
_SAY_LEN = re.compile(r"\blen=(\d+)\b")
_TRIM = ".,;:)\"']>"                   # 引用尾部标点裁净（句读不入 id）

# 人话动词表（账本动词 → 界面词;宪法 #41: 界面只说人话）
VERB_ZH = {
    "add-goal": "立项", "add-scope": "圈定测试范围",
    "add-intent": "新增意图", "add-asset": "收录资产", "add-cred": "登记凭据",
    "add-fact": "记录事实", "add-finding": "报告发现", "add-evidence": "存证",
    "add-edge": "关联图谱", "set-intent-status": "更新意图状态",
    "matrix-init": "建立覆盖矩阵", "matrix-set": "更新覆盖格",
    "matrix-set-batch": "批量更新覆盖", "matrix-freeze": "冻结覆盖矩阵",
    "budget-log": "记录预算", "request:": "发出验证请求",
    "replay-probe": "复测验证",
}
_FALLBACK_ZH = "记录"


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_int(value, name):
    """参数归一为 int;None 透传,不可解析 → ValueError（路由层转 4xx）。"""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None,布尔无语义:%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数:%r" % (name, value))


def _pick_battle(battles, battle):
    """战选择: None=最新（战号最大）;归一战号;不存在 → None。"""
    if battle is None:
        return battles[-1]["id"] if battles else None
    n = _read_int(battle, "battle")
    return "battle-%d" % n if any(b["n"] == n for b in battles) else None


def _timeline_rows(battle_dir):
    """G-*/timeline.tsv 合并读取（gen 目录排序确定）→ [(row_no, cols)]。

    行号=合并后 1 起全序位（帧=行号语义与 /api/stream 帧 id 同轴——
    会话页 _ledger_timeline_rows 同构,此处本地只读实现,规则一字对齐）。
    """
    rows = []
    try:
        gens = sorted(n for n in os.listdir(battle_dir)
                      if n.startswith("G-")
                      and os.path.isdir(os.path.join(battle_dir, n)))
    except OSError:
        return []
    for gen in gens:
        text = _read_text(os.path.join(battle_dir, gen, "timeline.tsv"))
        if text is None:
            continue
        for line in text.splitlines():
            if line.strip():
                rows.append(line.split("\t"))
    return list(enumerate(rows, 1))


def _ev_anchors(battle_dir):
    """E-index.tsv → {EV id: 挂接发现号}（gen 序后者覆盖,事件溯源同义）。"""
    out = {}
    try:
        gens = sorted(n for n in os.listdir(battle_dir)
                      if n.startswith("G-")
                      and os.path.isdir(os.path.join(battle_dir, n)))
    except OSError:
        return out
    idx = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    for gen in gens:
        text = _read_text(os.path.join(battle_dir, gen, "E-index.tsv"))
        if text is None:
            continue
        for line in text.splitlines():
            cols = line.split("\t")
            if len(cols) <= idx["linked_finding"] or not cols[0].strip():
                continue
            out[cols[0].strip()] = cols[idx["linked_finding"]].strip()
    return out


def _classify(cols):
    """行分类: 'agent'|'operator'|None（不入播报流）。"""
    actor = cols[1] if len(cols) > 1 else ""
    event = cols[3] if len(cols) > 3 else ""
    verb = event.split(" ")[0] if event else ""
    if verb == OPERATOR_VERB:
        return "operator"
    if actor == AGENT_ACTOR:
        return "agent"
    return None


def _plain_text(event):
    """人话句: 已知动词译中文+余项原文;未知动词兜底「记录」;绝不裸出空句。"""
    parts = event.split()
    if not parts:
        return _FALLBACK_ZH
    verb, rest = parts[0], parts[1:]
    if verb.startswith("replay:"):                 # replay:EV-x:STATUS 整词
        return "复测通过" + (" " + " ".join(rest) if rest else "")
    zh = VERB_ZH.get(verb)
    if zh:
        return " ".join([zh] + rest) if rest else zh
    return " ".join([_FALLBACK_ZH] + parts)        # 未知动词: 兜底词+原文


def _ev_refs(event):
    """事件文提取 EV 引用（去重保序,尾标点裁净）。"""
    seen, out = set(), []
    for m in _EV_REF.findall(event):
        ev = m.rstrip(_TRIM)
        if ev and ev not in seen:
            seen.add(ev)
            out.append(ev)
    return out


def broadcast_view(battles_dir=None, battle=None, frame=None, tail=DEFAULT_TAIL,
                   stream_source=None):
    """播报投影 → {battle, battles, frame, latest_row, tail, rows, counts,
    stream_aligned, stream_goal}。

    只读零写入;战不存在 → {"error": ..., "battles": [...]};
    坏战号/坏帧值 → ValueError。
    stream_source: 服务器 --ledger-dir（SSE /api/stream 的账本源）——与所选战
    最新代目录同址时 stream_aligned=True（页面直连 SSE,行号同轴）;否则 False
    （页面回落轮询,诚实披露）。默认 None=不判（False）。
    """
    root = battles_dir if battles_dir is not None else default_battles_dir()
    battles = list_battles(root)
    frame_no = _read_int(frame, "frame")
    tail_no = DEFAULT_TAIL if tail is None else _read_int(tail, "tail")
    picked = _pick_battle(battles, battle)
    if picked is None and battle is not None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}

    rows, latest_row, stream_aligned, stream_goal = [], 0, False, ""
    if picked is not None:
        battle_dir = os.path.join(root, picked)
        stream_goal = _latest_gen(battle_dir)
        stream_aligned = bool(
            stream_source and stream_goal and
            os.path.realpath(os.path.join(battle_dir, stream_goal))
            == os.path.realpath(str(stream_source)))
        anchors = _ev_anchors(battle_dir)
        for no, cols in _timeline_rows(battle_dir):
            latest_row = no
            kind = _classify(cols)
            if kind is None:
                continue
            if frame_no is not None and not no < frame_no:
                continue
            event = cols[3] if len(cols) > 3 else ""
            item = {"row": no,
                    "ts": cols[0] if cols else "",
                    "kind": kind,
                    "actor": cols[1] if len(cols) > 1 else "",
                    "phase": cols[2] if len(cols) > 2 else "",
                    "text": _plain_text(event),
                    "event": event,
                    "len": "",
                    "evidence": [{"id": ev, "finding": anchors.get(ev, "")}
                                 for ev in _ev_refs(event)]}
            if kind == "operator":
                m = _SAY_LEN.search(event)
                item["len"] = int(m.group(1)) if m else 0
                item["text"] = "操作员指令（%d 字·经指令通道下发）" % item["len"]
            rows.append(item)
        rows = rows[-max(0, tail_no):] if tail_no else []

    return {"battle": ({"id": picked, "n": int(_BATTLE_DIR.match(picked).group(1))}
                       if picked else None),
            "battles": battles,
            "frame": frame_no,
            "latest_row": latest_row,
            "tail": tail_no,
            "rows": rows,
            "stream_aligned": stream_aligned,
            "stream_goal": stream_goal,
            "counts": {"agent": sum(1 for r in rows if r["kind"] == "agent"),
                       "operator": sum(1 for r in rows if r["kind"] == "operator"),
                       "shown": len(rows)}}


def _latest_gen(battle_dir):
    """战目录最新代目录名（G-* 自然序,server._latest_gen 同律）;无=None。"""
    try:
        gens = sorted(n for n in os.listdir(battle_dir)
                      if n.startswith("G-")
                      and os.path.isdir(os.path.join(battle_dir, n)))
    except OSError:
        return None
    return gens[-1] if gens else None


# ------------------------------------------------------- include 挂载口（T1 同形）--

ROUTE_BROADCAST = "/api/v2/broadcast.json"
ROUTES = {ROUTE_BROADCAST: None}      # 尾部赋真身（前向引用）


def broadcast_route(query, ledger_dir=None, battles_dir=None):
    """路由适配层: query dict → (status, payload)。

    错误映射（session_api/_serve_session_battle 先例）: ValueError=422（坏参）,
    error 形=404（战不存在）;正常=200。会话门不在此层——include 挂载点
    （UI-1 api_pages.py）先过 Handler._session_ok 再分发,本函数不重复判。
    """
    try:
        payload = broadcast_view(
            battles_dir=battles_dir or None,
            battle=query.get("battle"),
            frame=query.get("frame"),
            tail=query.get("tail"),
            stream_source=ledger_dir or None)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_BROADCAST] = broadcast_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。

    UI-1 挂法（tests/test_webui_pagespec_broadcast.py _V2MountHandler 钉）:
        dispatch(path, query, server.ledger_dir, battles_dir=server.battles_dir)
    """
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir, battles_dir=battles_dir)
