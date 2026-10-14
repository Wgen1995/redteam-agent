# -*- coding: utf-8 -*-
"""v0.8 Task C：trace 只读检索——battles runner 日志 + timeline.tsv 的字面量子串搜索。

契约（docs/superpowers/plans/2026-10-11-v08-artex-borrow.md Task C）：
- 只读：search() 绝不写任何文件（含临时），数据源只以 r 模式 open；
- 仅 literal substring（`pattern in line`）：本模块永不 import re——正则元字符
  （.*、(、$、灾难回溯串）一律按字面处理，ReDoS 在此没有引擎可炸；
- 命中行附上下文各 2 行（CONTEXT=2，文件首尾自然裁齐）；
- scope="runner_logs"|"timeline"|"both"；battle=None 全战，或 int N / "N" / "battle-N"；
- last=N 只保留最近 N 条命中（文件序+行序取末尾 N 条）；None=不截断；0=空；
- battles_dir 路径注入：缺省 TANYIN_HOME（或 ~/.tanyin）/battles，同 scripts/battle.py BASE。

数据源布局（scripts/battle.py paths() 镜像）：
- runner 日志：battle-N/{opencode-run.log, opencode-run.log.runner.tsv, runner.out}
- timeline：battle-N/<gen>/timeline.tsv（walk 发现）

hit 结构：{"source", "file"(battles_dir 相对路径), "line_no"(1 起), "line",
"before"(<=2), "after"(<=2)}；逐文件流式扫描（deque 有界上下文，巨日志内存不胀），
输出按文件相对路径序 + 行序确定排列。
"""
import os
from collections import deque

SCOPES = ("runner_logs", "timeline", "both")
RUNNER_LOG_NAMES = ("opencode-run.log", "opencode-run.log.runner.tsv", "runner.out")
TIMELINE_NAME = "timeline.tsv"
CONTEXT = 2


def default_battles_dir():
    """battles 根缺省：TANYIN_HOME 可覆盖（与 scripts/battle.py BASE 同源）。"""
    home = os.environ.get("TANYIN_HOME") or os.path.join(os.path.expanduser("~"), ".tanyin")
    return os.path.join(home, "battles")


def _battle_dir_name(battle):
    """battle 参数归一为 'battle-N'；None 透传（=全部战）。"""
    if battle is None:
        return None
    if isinstance(battle, bool):
        raise TypeError("battle 需要 int/str/None，bool 无战号语义：%r" % (battle,))
    if isinstance(battle, int):
        n = battle
    elif isinstance(battle, str):
        s = battle[7:] if battle.startswith("battle-") else battle
        try:
            n = int(s)
        except ValueError:
            raise ValueError("battle 无法解析为战号：%r" % (battle,))
    else:
        raise TypeError("battle 需要 int/str/None：%r" % (battle,))
    return "battle-%d" % n


def _battle_homes(battles_dir, battle):
    """待搜战目录列表（排序确定）；battle 指定但不存在 -> 空（不炸）。"""
    name = _battle_dir_name(battle)
    if name is not None:
        home = os.path.join(battles_dir, name)
        return [home] if os.path.isdir(home) else []
    try:
        entries = sorted(os.listdir(battles_dir))
    except OSError:
        return []
    return [os.path.join(battles_dir, e) for e in entries
            if e.startswith("battle-") and os.path.isdir(os.path.join(battles_dir, e))]


def _source_files(battles_dir, homes, scope):
    """(相对路径, 绝对路径, source) 三元组列表，按相对路径排序。"""
    found = []
    for home in homes:
        if scope in ("runner_logs", "both"):
            for nm in RUNNER_LOG_NAMES:
                p = os.path.join(home, nm)
                if os.path.isfile(p):
                    found.append((p, "runner_logs"))
        if scope in ("timeline", "both"):
            for dirpath, dirnames, filenames in os.walk(home):
                dirnames.sort()
                if TIMELINE_NAME in filenames:
                    found.append((os.path.join(dirpath, TIMELINE_NAME), "timeline"))
    triples = [(os.path.relpath(p, battles_dir), p, src) for p, src in found]
    triples.sort(key=lambda t: t[0])
    return triples


def _scan(path, pattern):
    """流式扫描单文件 -> [hit, ...]；before 用 deque(maxlen)，after 用待填队列（均摊 O(1)/行）。"""
    hits = []
    pending = deque()   # after 尚未填满的 hit 下标（老的先填满，队列出列）
    before = deque(maxlen=CONTEXT)
    with open(path, encoding="utf-8", errors="replace") as f:
        for no, raw in enumerate(f, 1):
            text = raw.rstrip("\n")
            while pending and len(hits[pending[0]]["after"]) >= CONTEXT:
                pending.popleft()
            for i in pending:
                hits[i]["after"].append(text)
            if pattern in text:
                hits.append({"line_no": no, "line": text,
                             "before": list(before), "after": []})
                pending.append(len(hits) - 1)
            before.append(text)
    return hits


def search(pattern, scope="both", battle=None, last=None, battles_dir=None):
    """只读检索 battles runner 日志 + timeline.tsv——契约见模块 docstring。"""
    if not isinstance(pattern, str):
        raise TypeError("pattern 需要字符串（literal substring，无 regex）：%r" % (pattern,))
    if scope not in SCOPES:
        raise ValueError("scope 需要 %s 之一：%r" % ("/".join(SCOPES), scope))
    if last is not None:
        if isinstance(last, bool) or not isinstance(last, int):
            raise TypeError("last 需要 int 或 None：%r" % (last,))
        if last < 0:
            raise ValueError("last 不能为负：%d" % last)
    root = battles_dir if battles_dir is not None else default_battles_dir()
    if not os.path.isdir(root):
        return []
    hits = []
    for rel, p, src in _source_files(root, _battle_homes(root, battle), scope):
        for h in _scan(p, pattern):
            h["source"] = src
            h["file"] = rel
            hits.append(h)
    if last is not None:
        hits = hits[-last:] if last > 0 else []
    return hits
