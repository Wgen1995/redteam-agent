# -*- coding: utf-8 -*-
"""api_v2_retest（T3·P5.5）——复测页签只读投影，路由 /api/v2/retest.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制（api_pages.py，
UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_retest.py（_V2MountHandler）：
会话门复用 Handler._session_ok，缺会话=401 JSON。

数据单源（spec §P5.5：findings 复测域+重放日志）：
  复测队列  = findings（active 行）× timeline replay-probe 行归并——
              发现ID/上次结果/距上次/客户反馈（feedback 行文含 FD 号）/立即复测；
  复测历史  = 每发现的逐次重放（时间/结果/差异/触发方式[手动/自动复测]/耗时），
              timeline 行 × replay/<EV>/<n>.json 逐次对齐（api_v2_findings 同律）。

多代合并律（broadcast 同构）：battle-N/G-* 逐代扫描，G 号自然序（G-r2<G-r10，
server._latest_gen 同律非字典序）；表行同 id 后代胜（事件溯源同义）；timeline
全行合并编全局行号。战场钟 now_ref=全账最大行时刻（距上次=确定性推算，不取墙钟）。

差异律（诚实法条）：逐次与上次比——首次=「首测基线」；此后 verdict 变化入文；
verdict 同而 replay JSON 状态码漂移亦入文（200 → 500）；两侧任一缺 JSON=只比
verdict。距上次：未复测按首次发现时刻起算。
"""
import json
import os
import re

from ledger import core
from ledger.enforce import parse_ts
from ledger.session_view import list_battles

ROUTE_RETEST = "/api/v2/retest.json"
ROUTES = {ROUTE_RETEST: None}                        # 尾部赋真身（前向引用）

_REPLAY_PAT = re.compile(r"replay-probe (\S+) verdict=(\S+)")   # tanyin-replay 同形
_FEEDBACK_PAT = re.compile(r"feedback|客户反馈", re.I)
_TRIGGER_AUTO = ("复测", "auto", "retest")
_VERDICT_ZH = {
    "reproduced": "复现（漏洞仍在）",
    "not-reproduced": "未复现（疑似已修复）",
    "env-diff": "未复现·环境差异",
    "manual": "人工判定",
}


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


def _safe_epoch(ts):
    """parse_ts 容错包裹（坏行=None；enforce.parse_ts 单源）。"""
    try:
        return parse_ts(ts) if ts else None
    except (ValueError, TypeError):
        return None


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


def _read_dirs(battle_dir, gens):
    """读目录序：有 G-* 代=逐代目；无（单账本回落）=账本目自身。"""
    if gens:
        return [os.path.join(battle_dir, g) for g in gens]
    return [battle_dir] if battle_dir else []


def _merge_by_id(battle_dir, gens, tname):
    """表行跨代合并：同 id 后代胜，保首现次序 → [(id, cols)]。"""
    nf = len(core.TABLES[tname])
    by_id, order = {}, []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, tname), nf):
            key = cols[0].strip()
            if not key:
                continue
            if key not in by_id:
                order.append(key)
            by_id[key] = cols
    return [(k, by_id[k]) for k in order]


def _merged_timeline(battle_dir, gens):
    """全代 timeline 合并 → [(全局行号, cols, 源目录)]（行号供页面账本锚定）。"""
    nf = len(core.TABLES["timeline.tsv"])
    out = []
    for d in _read_dirs(battle_dir, gens):
        for cols in _read_tsv_rows(os.path.join(d, "timeline.tsv"), nf):
            out.append((cols, d))
    return [(no, item[0], item[1]) for no, item in enumerate(out, 1)]


def _trigger(actor):
    a = (actor or "").strip().lower()
    return "自动复测" if any(k in a for k in _TRIGGER_AUTO) else "手动"


def _human_dur(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    if days:
        return "%d天%d小时" % (days, hours)
    if hours:
        return "%d小时%d分" % (hours, mins)
    if mins:
        return "%d分钟" % mins
    return "%d秒" % seconds


def _dur_text(diff_s):
    return _human_dur(diff_s) if diff_s is not None else "—"


def _replay_json(gen_dir, ev_id, seq):
    p = os.path.join(gen_dir, "replay", ev_id, "%d.json" % seq)
    text = _read_text(p)
    if text is None:
        return {}
    try:
        obj = json.loads(text)
    except ValueError:
        return {}
    return obj if isinstance(obj, dict) else {}


# ------------------------------------------------------------------ 投影 --

def retest_view(battles_dir=None, battle=None, ledger_dir=None):
    """复测页签投影 → {battle, battles, goal, now_ref, counts, queue[]}。

    queue 每行：id/title/impact/last_verdict(+zh)/last_at/since_last_s/_text/
    has_feedback/feedback_count/runs/replayable/evidence_count/history[]。
    战不存在 → {"error":..., "battles":[...]}；坏战号 → ValueError。
    """
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}
    gens = _gens(battle_dir) if battle_dir else []
    goal = gens[-1] if gens else os.path.basename(os.path.normpath(str(battle_dir or "")))

    tf = {f: i for i, f in enumerate(core.TABLES["findings.tsv"])}
    tei = {f: i for i, f in enumerate(core.TABLES["E-index.tsv"])}
    findings = _merge_by_id(battle_dir, gens, "findings.tsv")
    evidence = dict(_merge_by_id(battle_dir, gens, "E-index.tsv"))
    timeline = _merged_timeline(battle_dir, gens)
    tle = {f: i for i, f in enumerate(core.TABLES["timeline.tsv"])}

    # replay 事件单遍扫描（全局行号直接入项，携 gen 供 replay JSON 定位）
    runs_by_ev = {}
    for no, cols, gen in timeline:
        m = _REPLAY_PAT.search(cols[tle["event"]])
        if not m:
            continue
        runs_by_ev.setdefault(m.group(1), []).append(
            {"verdict": m.group(2), "at": cols[tle["timestamp"]],
             "actor": cols[tle["actor"]], "row": no, "gen": gen})

    # EV → 发现 反指（evidence_ids ∪ linked_finding）
    evs_of = {}
    for fid, cols in findings:
        ids = [x.strip() for x in cols[tf["evidence_ids"]].split(",") if x.strip()]
        evs_of[fid] = set(ids)
    for ev_id, cols in evidence.items():
        fid = cols[tei["linked_finding"]].strip()
        if fid and fid in evs_of:
            evs_of[fid].add(ev_id)

    # 客户反馈行（feedback 文案 + 含 FD 号才算该发现的反馈）
    feedback = {}
    for _no, cols, _gen in timeline:
        ev = cols[tle["event"]]
        if not _FEEDBACK_PAT.search(ev):
            continue
        for fid, _c in findings:
            if fid in ev:
                feedback.setdefault(fid, []).append(cols[tle["timestamp"]])

    now_ref = max((cols[tle["timestamp"]] for _no, cols, _g in timeline), default="")
    now_s = _safe_epoch(now_ref)

    queue = []
    runs_total = 0
    for fid, cols in findings:
        if cols[tf["status"]].strip() and cols[tf["status"]].strip() != "active":
            continue
        ev_ids = sorted(evs_of.get(fid, set()))
        hist = []
        for ev_id in ev_ids:
            seen_gen = {}                       # seq 按代计（replay/<EV>/<n>.json 代内序）
            for r in runs_by_ev.get(ev_id, []):
                g = r["gen"]
                seen_gen[g] = seen_gen.get(g, 0) + 1
                j = _replay_json(g, ev_id, seen_gen[g])
                hist.append({"ev_id": ev_id, "at": r["at"], "verdict": r["verdict"],
                             "trigger": _trigger(r["actor"]), "row": r["row"],
                             "duration_ms": j.get("elapsed_ms"),
                             "status": j.get("status")})
        hist.sort(key=lambda h: h["at"])
        for i, h in enumerate(hist):
            h["seq"] = i + 1
            h["diff"] = _diff(hist, i)
        runs_total += len(hist)
        fb = feedback.get(fid, [])
        last = hist[-1] if hist else None
        anchor = (last or {}).get("at") or cols[tf["created"]]
        anc_s = _safe_epoch(anchor)
        since = int(now_s - anc_s) if (now_s is not None and anc_s is not None) else None
        queue.append({
            "id": fid, "title": cols[tf["title"]], "impact": cols[tf["impact"]],
            "created": cols[tf["created"]],
            "last_verdict": last["verdict"] if last else "",
            "last_verdict_zh": (_VERDICT_ZH.get(last["verdict"], last["verdict"])
                                if last else "未复测"),
            "last_at": last["at"] if last else "",
            "since_last_s": since,
            "since_last_text": _dur_text(since),
            "has_feedback": bool(fb), "feedback_count": len(fb),
            "runs": len(hist), "replayable": bool(ev_ids),
            "evidence_count": len(ev_ids),
            "history": hist,
        })
    # 队序：可复测（有证据）先列；同组内最久未复测先列（确定性）
    queue.sort(key=lambda f: (not f["replayable"], f["last_at"] or f["created"], f["id"]))

    return {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles, "goal": goal, "now_ref": now_ref,
        "counts": {
            "findings": len(queue),
            "replayable": sum(1 for f in queue if f["replayable"]),
            "runs_total": runs_total,
            "with_feedback": sum(1 for f in queue if f["has_feedback"]),
            "never_retested": sum(1 for f in queue if f["runs"] == 0),
        },
        "queue": queue,
    }


def _diff(hist, i):
    """第 i 次与上次的差异文；首测=基线。verdict 变化主文，状态码漂移附文。"""
    cur = hist[i]
    if i == 0:
        return "首测基线"
    prev = hist[i - 1]
    parts = []
    if cur["verdict"] != prev["verdict"]:
        parts.append("%s → %s" % (prev["verdict"], cur["verdict"]))
    if (cur.get("status") is not None and prev.get("status") is not None
            and cur["status"] != prev["status"]):
        parts.append("状态码 %s → %s" % (prev["status"], cur["status"]))
    return "；".join(parts) if parts else "无变化"


def retest_route(query, ledger_dir=None, battles_dir=None):
    """路由层：ValueError=422；error 形=404；正常=200。"""
    try:
        payload = retest_view(battles_dir=battles_dir, battle=query.get("battle"),
                              ledger_dir=ledger_dir)
    except ValueError as e:
        return 422, {"error": str(e)}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_RETEST] = retest_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
