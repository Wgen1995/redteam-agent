# -*- coding: utf-8 -*-
"""state.md v2 冻结格式（批次 3 接口，02a 终审补全 5 授权冻结）。
职责单一：键序/解析/原子写/200 行硬顶。语义（锁/对账/重建）在 write_cmds 与 phases_engine。
批次 6 T7（G-5·裁决 F）：锁四字段 lock_host/lock_pid/lock_boot/lock_since 为可选后缀
（LOCK_KEY_ORDER）——v1 旧锁（无四字段）解析容忍照常；带锁形=14 键（FULL_KEY_ORDER）。
锁字段值由 lock_v2.lock_fields 单源产出，本模块纯格式层（解析/键序/原子写，不造锁）。"""
import os

from . import core

KEY_ORDER = ["revision", "goal", "phase", "round", "session", "session_status",
             "spawn", "updated", "resume_kit", "snapshot"]
LOCK_KEY_ORDER = ["lock_host", "lock_pid", "lock_boot", "lock_since"]
FULL_KEY_ORDER = KEY_ORDER + LOCK_KEY_ORDER
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
    keys = list(fields)
    if fields and keys not in (KEY_ORDER, FULL_KEY_ORDER):
        # v1 十键 / v2 十四键（锁后缀须全有或全无；残缺=畸形→对账重建保守路径）
        errs.append("固定段键集/键序不符: %s" % keys)
    if fields and not errs:
        if not fields["revision"].isdigit():
            errs.append("revision 非整数: %r" % fields["revision"])
        if "lock_pid" in fields and not fields["lock_pid"].isdigit():
            errs.append("lock_pid 非整数: %r" % fields["lock_pid"])
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
    # 保守按 v2 十四键形预检（批次 6 T7：带锁形多 4 行；常规面余量只增不减）
    return 1 + len(FULL_KEY_ORDER) + 1 + len([h for h in handoff]) > MAX_LINES


def write_state(path, fields, handoff):
    # 键形二态：v1 十键原样；显式带锁四字段（lock_host 在场）=v2 十四键。
    # 写者不造锁——锁字段由调用方经 lock_v2.lock_fields 产出（checkpoint
    # --with-lock-v2 内部通道；夹具/测试手置锁同形）。
    keys = FULL_KEY_ORDER if "lock_host" in fields else KEY_ORDER
    body = ["%s: %s" % (k, fields[k]) for k in keys] + [HEADER] + list(handoff)
    if len(body) > MAX_LINES:
        raise ValueError("state.md 超行数硬顶 %d（当前 %d）——压缩 handoff"
                         % (MAX_LINES, len(body)))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:   # LF 字节纪律
        f.write("\n".join(body) + "\n")
    os.replace(tmp, path)   # kill -9 半写兜底：要么旧版要么新版，无第三态
