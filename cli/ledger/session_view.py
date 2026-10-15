# -*- coding: utf-8 -*-
"""v0.9d Ship S · 会话页只读装配——runner transcript 投影 + 介入/注入事件穿插。

契约（docs/superpowers/plans/2026-10-15-v09d-ui.md Ship S 节 + walk-tanyin §四4 +
0-dsh §五2 工具卡三态披露行）：本模块只读零写入（一切文件 r 模式 open）、
禁 datetime.now（输出确定性：全取文件序）、Python 3.9 纯 stdlib。

数据源（trace_search 同源文件名，battle 目录实勘 battle-42）：
- transcript：battle-N/opencode-run.log（opencode TUI 捕获，含 ANSI 色码）；
- runner 生命周期：battle-N/opencode-run.log.runner.tsv（BOOT/LAUNCH/DIRECTIVE/
  RESTART/PROGRESS/EXIT/DONE，wall 钟真实时间戳）；
- 账本 timeline：battle-N/G-*/timeline.tsv（场景钟；G-* 子目录即 gen，
  metrics._gen_of 同命名法）。

transcript 解析律（TUI 捕获无 tool_use/result id，按行首标记归块——实勘计数：
ARROW 后随 TEXT 23 例均为战士叙事而非工具输出，故立不对称规则）：
- "> " 行 = 轮头（重启分段，ARTEX transcript round 分隔同义）；
- "→ X ..." = 调用卡（state=ok）：TUI 不回显工具体，卡不吞正文；
- "$ cmd"  = 命令卡（state=bash）：输出吞至下一标记行（含内部空行，尾部空行裁净）；
- "✗ X failed" = 失败卡（state=error）：只收紧随的 "Error..." 行，正文归文本块；
- 其余 TEXT 行 = 文本块（连续行合并，含段内空行）。
三态即 dsh 工具卡披露律的只读投影：折叠=标题首行+状态徽章，展开=输出体。

穿插律（介入/注入事件穿插，两路单源）：
- runner 路注入：LAUNCH/RESTART 各开一段（段号=轮号锚）；非 PROGRESS 行按段
  插轮尾（段 0 的 BOOT 插首轮头）——DIRECTIVE=指令注入、RESTART=介入重启；
- timeline 路介入：actor ∈ INTERVENTION_ACTORS（总控/canary/egress——平台执法
  与操作者介入；CLI=战士写账、replay=验证环，皆非介入）的行，按「首个
  timeline 计数 ≥ 行号 的 PROGRESS」所在段锚轮尾（数据推导：该行在该 PROGRESS
  报点时已确认在账）；无锚（无 runner/未覆盖）→ 尾轮兜底。

已知局限（诚实声明）：$ 命令卡吞至下标记，其后紧随的战士叙事会折入卡输出区
（展开可见，零丢失）；场景钟与 wall 钟不同源，穿插位置是段锚而非钟表对齐。
"""
import os
import re

# battles 根缺省与 trace_search.default_battles_dir 同源（TANYIN_HOME 可覆盖）
from ledger.trace_search import RUNNER_LOG_NAMES, default_battles_dir  # noqa: F401

RUNNER_TSV_NAME = "opencode-run.log.runner.tsv"
TRANSCRIPT_NAME = "opencode-run.log"
INTERVENTION_ACTORS = ("总控", "canary", "egress")
PROGRESS = "PROGRESS"
SEGMENT_STARTERS = ("LAUNCH", "RESTART")

_ANSI = re.compile("\x1b\[[0-9;]*m")
_BATTLE = re.compile(r"^battle-(\d+)$")
_TL_COUNT = re.compile(r"timeline=(\d+)")
_RECALL = re.compile(r"recall=([0-9.]+) \((\d+)/(\d+)\)")
_CHAIN = re.compile(r"verify-chain[:：]\s*(PASS|FAIL)")

MARK_HEAD = "> "
MARK_ARROW = "\u2192 "
MARK_CROSS = "\u2717 "
MARK_BASH = "$ "
MARK_ERR = "Error"


def strip_ansi(text):
    """剥 ANSI SGR 色码（TUI 捕获残留；只会读，不会改源文件）。"""
    return _ANSI.sub("", text)


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


# --- transcript 投影 -----------------------------------------------------------


def _is_marker(line):
    return line.startswith((MARK_ARROW, MARK_CROSS, MARK_BASH, MARK_HEAD))


def parse_transcript(text):
    """transcript 文本 → [{head, entries:[...]}]（轮序+块序全文件序，确定性）。

    entries：{"kind":"text","lines":[...]}
            |{"kind":"tool","state":"ok|error|bash","tool","title"[,"cmd"],"output":[...]}
    """
    rounds, cur, cur_entries = [], None, []

    def _flush_round():
        nonlocal cur_entries
        if cur is not None or cur_entries:
            rounds.append({"head": cur or "", "entries": cur_entries})
        cur_entries = []

    lines = [strip_ansi(l) for l in text.splitlines()]
    i, n = 0, len(lines)
    text_run = []

    def _flush_text():
        nonlocal text_run
        while text_run and not text_run[-1].strip():
            text_run.pop()                          # 尾部空行裁净
        if text_run:
            cur_entries.append({"kind": "text", "lines": list(text_run)})
        text_run = []

    while i < n:
        line = lines[i]
        if line.startswith(MARK_HEAD):              # 轮头：新开一轮
            _flush_text()
            _flush_round()
            cur = line
            i += 1
            continue
        if line.startswith(MARK_ARROW):             # 调用卡：不吞正文
            _flush_text()
            title = line[len(MARK_ARROW):].strip()
            cur_entries.append({"kind": "tool", "state": "ok",
                                "tool": title.split(" ", 1)[0] if title else "",
                                "title": title, "output": []})
            i += 1
            continue
        if line.startswith(MARK_CROSS):             # 失败卡：只收 Error... 行
            _flush_text()
            title = line[len(MARK_CROSS):].strip()
            out = []
            j = i + 1
            while j < n and lines[j].startswith(MARK_ERR):
                out.append(lines[j])
                j += 1
            cur_entries.append({"kind": "tool", "state": "error",
                                "tool": title.split(" ", 1)[0] if title else "",
                                "title": title, "output": out})
            i = j
            continue
        if line.startswith(MARK_BASH):              # 命令卡：吞至下一标记
            _flush_text()
            cmd = line[len(MARK_BASH):].strip()
            out = []
            j = i + 1
            while j < n and not _is_marker(lines[j]):
                out.append(lines[j])
                j += 1
            while out and not out[-1].strip():
                out.pop()
            cur_entries.append({"kind": "tool", "state": "bash", "tool": "Bash",
                                "title": cmd, "cmd": cmd, "output": out})
            i = j
            continue
        text_run.append(line)                       # 文本块行（含段内空行）
        i += 1
    _flush_text()
    _flush_round()
    if not rounds and text:
        rounds.append({"head": "", "entries": []})   # 空容错：有文本无轮头
    return rounds


# --- runner 生命周期 ------------------------------------------------------------


def parse_runner_tsv(text):
    """runner.tsv 文本 → [{ts,kind,detail}]（文件序）；坏行跳过多代容错。"""
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        ts, kind = parts[0].strip(), parts[1].strip()
        detail = parts[2] if len(parts) > 2 else ""
        rows.append({"ts": ts, "kind": kind, "detail": detail.strip()})
    return rows


def _segments(rows):
    """runner 行 → [(row, seg)]；LAUNCH/RESTART 开新段（段号=轮号锚，BOOT=段0）。"""
    out, seg = [], 0
    for r in rows:
        if r["kind"] in SEGMENT_STARTERS:
            seg += 1
        out.append((r, seg))
    return out


def _progress_counts(rows):
    """PROGRESS 行 → [(seg, timeline_count)]（timeline 行号→段锚的查表键）。"""
    out = []
    for r, seg in _segments(rows):
        if r["kind"] == PROGRESS:
            m = _TL_COUNT.search(r["detail"])
            if m:
                out.append((seg, int(m.group(1))))
    return out


# --- timeline 介入事件 -----------------------------------------------------------


def _ledger_timeline_rows(battle_dir):
    """G-*/timeline.tsv 合并读取（gen 目录排序确定）→ [(row_no, [cols])]。"""
    rows, gens = [], []
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


def _interventions(battle_dir):
    """timeline 介入行 → [{row, ts, actor, phase, event}]（行序确定）。"""
    out = []
    for no, cols in _ledger_timeline_rows(battle_dir):
        actor = cols[1] if len(cols) > 1 else ""
        if actor not in INTERVENTION_ACTORS:
            continue
        out.append({"row": no,
                    "ts": cols[0] if cols else "",
                    "actor": actor,
                    "phase": cols[2] if len(cols) > 2 else "",
                    "event": cols[3] if len(cols) > 3 else ""})
    return out


# --- battle 元信息 ----------------------------------------------------------------


def _battle_meta(battle_dir):
    """battle 元信息 → {id,n,mission,directive_bytes,settle,gen}（缺件降级）。"""
    name = os.path.basename(os.path.normpath(battle_dir))
    m = _BATTLE.match(name)
    doc = {"id": name if m else None,
           "n": int(m.group(1)) if m else None,
           "mission": "", "directive_bytes": None,
           "settle": None, "gen": None}
    mission = _read_text(os.path.join(battle_dir, "mission.txt"))
    if mission is not None:
        doc["mission"] = mission
    try:
        doc["directive_bytes"] = os.path.getsize(
            os.path.join(battle_dir, "directive.txt"))
    except OSError:
        pass
    settle_txt = _read_text(os.path.join(battle_dir, "settle-report.txt"))
    if settle_txt is not None:
        rm, cm = _RECALL.search(settle_txt), _CHAIN.search(settle_txt)
        if rm:
            hits, total = int(rm.group(2)), int(rm.group(3))
            doc["settle"] = {"recall": round(hits / total, 4) if total else 0.0,
                             "hits": hits, "total": total,
                             "chain": cm.group(1) if cm else ""}
    try:
        gens = sorted(n for n in os.listdir(battle_dir)
                      if n.startswith("G-")
                      and os.path.isdir(os.path.join(battle_dir, n)))
        doc["gen"] = gens[0] if gens else None
    except OSError:
        pass
    return doc


# --- 主装配 ------------------------------------------------------------------------


def _empty_doc():
    """无战空 shape（battle 目录不存在/battles 根无 battle-N：页面空态同源）。"""
    return {"battle": None,
            "runner": [], "rounds": [], "timeline_interventions": [],
            "stats": {"rounds": 0, "tools": 0, "bash": 0, "errors": 0,
                      "texts": 0, "interventions": 0, "lines": 0}}


def session_view(battle_dir):
    """单战会话装配（只读）→ {battle, runner, rounds, timeline_interventions, stats}。"""
    if not os.path.isdir(battle_dir):
        return _empty_doc()
    meta = _battle_meta(battle_dir)
    runner_rows = parse_runner_tsv(
        _read_text(os.path.join(battle_dir, RUNNER_TSV_NAME)) or "")
    rounds = parse_transcript(
        _read_text(os.path.join(battle_dir, TRANSCRIPT_NAME)) or "")
    inter = _interventions(battle_dir)

    seg_rows = _segments(runner_rows)
    prog = _progress_counts(runner_rows)

    def _round_entries(idx):
        """轮 idx（1 起）的 entries；无轮时借造伪空轮，越界夹末轮（兜底确定性）。"""
        if not rounds:
            rounds.append({"head": "", "entries": []})
        return rounds[min(max(idx, 1), len(rounds)) - 1]["entries"]

    # runner 路：段 0 头锚首轮；其余段尾锚（含 EXIT/DONE 落末段=末轮尾）；
    # LAUNCH/RESTART 本身即轮头 "> build" 的 runner 侧镜像，不再重复穿插
    for r, seg in seg_rows:
        if r["kind"] == PROGRESS or r["kind"] in SEGMENT_STARTERS:
            continue
        evt = {"kind": "event", "source": "runner", "ts": r["ts"],
               "event_kind": r["kind"], "detail": r["detail"]}
        if seg == 0:
            _round_entries(1).insert(0, evt)
        else:
            _round_entries(seg).append(evt)
    # timeline 路：首个 timeline 计数 ≥ 行号的 PROGRESS 段锚；无锚 → 尾轮兜底
    for iv in inter:
        seg_anchor = None
        for seg, cnt in prog:
            if cnt >= iv["row"]:
                seg_anchor = seg
                break
        evt = {"kind": "event", "source": "timeline", "ts": iv["ts"],
               "actor": iv["actor"], "phase": iv["phase"], "event": iv["event"],
               "row": iv["row"]}
        _round_entries(seg_anchor if seg_anchor is not None else len(rounds)
                       if rounds else 1).append(evt)

    stats = {"rounds": len(rounds), "tools": 0, "bash": 0, "errors": 0,
             "texts": 0, "interventions": 0, "lines": 0}
    txt = _read_text(os.path.join(battle_dir, TRANSCRIPT_NAME))
    stats["lines"] = len(txt.splitlines()) if txt else 0
    for rnd in rounds:
        for e in rnd["entries"]:
            if e["kind"] == "tool":
                stats["tools"] += 1
                if e["state"] == "bash":
                    stats["bash"] += 1
                elif e["state"] == "error":
                    stats["errors"] += 1
            elif e["kind"] == "text":
                stats["texts"] += 1
            elif e["kind"] == "event":
                stats["interventions"] += 1
    return {"battle": meta, "runner": runner_rows, "rounds": rounds,
            "timeline_interventions": inter, "stats": stats}


def list_battles(battles_dir=None):
    """battles 根 → [{id, n}]（战号升序；非 battle-N 目录跳过）。"""
    root = battles_dir if battles_dir is not None else default_battles_dir()
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []
    out = []
    for name in names:
        m = _BATTLE.match(name)
        if m and os.path.isdir(os.path.join(root, name)):
            out.append({"id": name, "n": int(m.group(1))})
    out.sort(key=lambda b: b["n"])
    return out


def session_api(battles_dir=None, battle=None):
    """server /api/session.json 单源入口（可注入路径可测）。

    battle=None → 最新战（战号最大）；int/"N"/"battle-N" 归一；战不存在 →
    {"error":..., "battles":[...]}（服务端转 404）；非数战号 → ValueError。
    """
    root = battles_dir if battles_dir is not None else default_battles_dir()
    battles = list_battles(root)
    if battle is None:
        picked = battles[-1]["id"] if battles else None
    else:
        if isinstance(battle, bool):
            raise ValueError("battle 需要 int/str/None，bool 无战号语义：%r" % (battle,))
        if isinstance(battle, int):
            n = battle
        elif isinstance(battle, str):
            s = battle[7:] if battle.startswith("battle-") else battle
            try:
                n = int(s)
            except ValueError:
                raise ValueError("battle 无法解析为战号：%r" % (battle,))
        else:
            raise ValueError("battle 需要 int/str/None：%r" % (battle,))
        picked = "battle-%d" % n if any(b["n"] == n for b in battles) else None
        if picked is None:
            return {"error": "battle 不存在: %d" % n, "battles": battles}
    doc = (session_view(os.path.join(root, picked)) if picked
           else _empty_doc())
    doc["battles"] = battles
    return doc
