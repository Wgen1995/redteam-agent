# -*- coding: utf-8 -*-
"""state.md v2 冻结格式（批次 3 接口，02a 终审补全 5 授权冻结）。
职责单一：键序/解析/原子写/200 行硬顶。语义（锁/对账/重建）在 write_cmds 与 phases_engine。"""
import os

from . import core

KEY_ORDER = ["revision", "goal", "phase", "round", "session", "session_status",
             "spawn", "updated", "resume_kit", "snapshot"]
HEADER = "--- handoff ---"
MAX_LINES = 200
SESSION_STATUS = {"active", "released"}
SPAWN_VALUES = {"fresh", "auto", "manual"}


def parse_state(path):
    """→ (fields|None, handoff 行列表, errs)。文件缺失=(None, [], [])。
    固定段逐行 key: value（沿 check_cmds.h_state_rebuild 既有 revision 解析范式扩展）。"""
    if not os.path.isfile(path):
        return None, [], []
    fields, handoff, errs, in_body = {}, [], [], False
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if len(lines) > MAX_LINES:
        errs.append("state.md 行数 %d 超硬顶 %d" % (len(lines), MAX_LINES))
    for ln in lines:
        if ln.strip() == HEADER:
            in_body = True
            continue
        if in_body:
            handoff.append(ln)
            continue
        k, sep, v = ln.partition(":")
        if not sep:
            errs.append("固定段畸形行: %r" % ln)
            continue
        fields[k.strip()] = v.strip()
    if fields and list(fields) != KEY_ORDER:
        errs.append("固定段键集/键序不符: %s" % list(fields))
    if fields and not errs:
        if not fields["revision"].isdigit():
            errs.append("revision 非整数: %r" % fields["revision"])
        if fields["session_status"] not in SESSION_STATUS:
            errs.append("session_status 不在 {active,released}")
        if fields["spawn"] not in SPAWN_VALUES:
            errs.append("spawn 不在 {fresh,auto,manual}")
        if fields["phase"] and fields["phase"] not in core.GATE_ORDER:
            errs.append("phase 不在九门: %r" % fields["phase"])
    return fields, handoff, errs


def snapshot_from_session(s):
    from . import query_cmds as q
    pend = sum(1 for r in q.latest_intents(s).values()
               if r[q._idx("intents.tsv", "status")] == "pending")
    un = len(q.unconsumed_facts(s))
    gaps = len(q.matrix_gap_cells(s))
    t = q.budget_tree(s)
    left = ""
    if t["goal"] and t["goal"]["limit"]["token"] is not None:
        left = "%d" % int(t["goal"]["limit"]["token"] - t["goal"]["used"]["token"])
    return "intents_pending=%d;facts_unconsumed=%d;matrix_gaps=%d;budget_token_left=%s" \
        % (pend, un, gaps, left)


def would_overflow(handoff):
    return 1 + len(KEY_ORDER) + 1 + len([h for h in handoff]) > MAX_LINES


def write_state(path, fields, handoff):
    body = ["%s: %s" % (k, fields[k]) for k in KEY_ORDER] + [HEADER] + list(handoff)
    if len(body) > MAX_LINES:
        raise ValueError("state.md 超行数硬顶 %d（当前 %d）——压缩 handoff"
                         % (MAX_LINES, len(body)))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:   # LF 字节纪律
        f.write("\n".join(body) + "\n")
    os.replace(tmp, path)   # kill -9 半写兜底：要么旧版要么新版，无第三态
