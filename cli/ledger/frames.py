# -*- coding: utf-8 -*-
"""W2·C:G2 runner 事件帧化+call_id——会话事件帧契约（NDJSON，schema_version=1）。

来源：docs/reviews/2026-10-18-realign/C-zhulong-multica-全件对齐.md G2——
「opencode TUI 文本捕获无 tool_use/result id（session_view.py:15），格式漂移
即解析崩；无取消协商」。本模块=帧化自家 runner 契约的数据面单源：

- 帧形：一行一个 JSON 对象；锚键 schema_version（读侧闸：非本版帧跳过，
  多代容错同 parse_runner_tsv）；seq=文件内序（append 时按存量行数+1 铸）。
- kind 两族：runner 生命周期帧（BOOT/LAUNCH/RESTART/…，runner.tsv 同词面，
  由 tanyin-runner log_event 双写——先写帧后杀的审计底座）；战士帧
  WARRIOR_KINDS=round/text/tool_use/tool_result（tool_use↔tool_result 以
  call_id 精确配对——修「按行首标记猜」脆弱点，W6 工具卡渲染可直接消费）。
- 投影律：frames_to_rounds 输出与 session_view.parse_transcript 同构
  （[{head, entries:[...]}]）；未回结果的 use=开卡（state=open，不伪造 ok）；
  无主 result=orphan 卡保留；生命周期帧不入条目（session_view 另从
  runner.tsv 穿插，双计防御）。
- 纪律：Python 3.9 纯 stdlib；append 尽力而为（帧=审计镜像，runner.tsv
  仍是第一事实源；写失败不阻 runner 主流程）。
"""
import json
import os

FRAMES_SCHEMA_VERSION = 1
FRAMES_SUFFIX = ".frames.ndjson"

# 战士面帧 kind（会话条目投影的唯一来源族）
WARRIOR_KINDS = ("round", "text", "tool_use", "tool_result")

# 结果帧 state 枚举（tool_result 帧）；tool_use 无 state（配对前不开判）
RESULT_STATES = ("ok", "error")


def dump_frame(ts, kind, *, call_id="", tool="", title="", detail="",
               text="", output=None, state=""):
    """铸帧 dict（不落盘；schema_version 锚+键序确定）。"""
    frame = {"schema_version": FRAMES_SCHEMA_VERSION, "ts": ts or "", "kind": kind,
             "call_id": call_id or ""}
    if tool:
        frame["tool"] = tool
    if title:
        frame["title"] = title
    if detail:
        frame["detail"] = detail
    if text:
        frame["text"] = text
    if output:
        frame["output"] = [str(l) for l in output]
    if state:
        frame["state"] = state
    return frame


def frames_path_for(runner_log):
    """runner.tsv 路径 → 同基名帧文件（opencode-run.log.runner.tsv →
    opencode-run.log.frames.ndjson=session_view.FRAMES_NAME 单源对齐）。"""
    base = runner_log[:-len(".runner.tsv")] if runner_log.endswith(".runner.tsv") \
        else os.path.splitext(runner_log)[0]
    return base + FRAMES_SUFFIX


def append_frame(path, ts, kind, **fields):
    """追加一帧（seq=存量行数+1；尽力而为：OSError 不抛——镜像面不阻主流程）。"""
    frame = dump_frame(ts, kind, **fields)
    try:
        n = 0
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as f:
                n = sum(1 for _ in f)
        frame["seq"] = n + 1
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(frame, ensure_ascii=False, sort_keys=True) + "\n")
        return frame
    except OSError:
        return None


def parse_frames(text):
    """帧文本 → [frame]（文件序；空行/非 JSON/非本版帧跳过——多代容错）。"""
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            frame = json.loads(line)
        except ValueError:
            continue
        if isinstance(frame, dict) and frame.get("schema_version") == FRAMES_SCHEMA_VERSION \
                and frame.get("kind"):
            out.append(frame)
    return out


def has_warrior_frames(frames):
    """战士帧在场判定（session_view 帧优先→标记法回落的切换键）。"""
    return any(f.get("kind") in WARRIOR_KINDS for f in frames)


def frames_to_rounds(frames):
    """战士帧 → [{head, entries:[...]}]（与 parse_transcript 同构）。

    round 帧开新轮（title=轮头）；条目先于首 round 帧 → 轮头 "" 容错轮
    （parse_transcript 空容错同义）；tool_use 即落卡（state=open），同
    call_id 的 tool_result 回填就地配对（paired=True；call_id 会话全局
    唯一→配对不受轮界切断，迟到结果回填原轮原卡）；无主 result=orphan 卡。
    """
    rounds, cur_entries = [], []
    head = None
    cards = {}   # call_id → 卡 dict（会话全局就地配对——不随轮重置）

    def _flush():
        nonlocal cur_entries
        if head is not None or cur_entries:
            rounds.append({"head": head if head is not None else "", "entries": cur_entries})
        cur_entries = []

    for f in frames:
        kind = f.get("kind")
        if kind == "round":
            _flush()
            head = str(f.get("title") or f.get("detail") or "")
        elif kind == "text":
            cur_entries.append({"kind": "text",
                                "lines": str(f.get("text") or "").splitlines()})
        elif kind == "tool_use":
            card = {"kind": "tool", "state": "open", "paired": False,
                    "call_id": str(f.get("call_id") or ""),
                    "tool": str(f.get("tool") or ""),
                    "title": str(f.get("title") or ""), "output": []}
            cur_entries.append(card)
            if card["call_id"]:
                cards[card["call_id"]] = card
        elif kind == "tool_result":
            cid = str(f.get("call_id") or "")
            state = f.get("state") if f.get("state") in RESULT_STATES else "ok"
            output = [str(l) for l in (f.get("output") or [])]
            card = cards.get(cid)
            if card is not None:
                card.update({"state": state, "output": output, "paired": True})
            else:
                cur_entries.append({"kind": "tool", "state": state, "paired": False,
                                    "orphan": True, "call_id": cid,
                                    "tool": str(f.get("tool") or ""),
                                    "title": str(f.get("title") or ""), "output": output})
    _flush()
    return rounds
