# -*- coding: utf-8 -*-
"""webui sse（v0.9a T2）——timeline 追尾生成器（线程模型轮询，无 asyncio）。

契约（docs/superpowers/plans/2026-10-11-tanyin-web-skeleton.md Task 2）：
先吐存量尾部 start_tail 条（id=1 起行号游标），再按 poll_interval 轮询文件增长，
增量行逐条成帧；空转 keepalive_s 无新行发 `: keepalive` 心跳帧（客户端断连侦测）。
帧形：id: <行号> + data: <JSON>（snapshot.row_to_event 同形载荷）+ 空行分隔。
只读律：本模块永不写 path；账本写方为 cli/ledger（原子整文件替换）。
"""
import json, time

from .snapshot import row_to_event

DEFAULT_POLL_S = 1.0
DEFAULT_KEEPALIVE_S = 15.0


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _complete_lines(text):
    """只取完整行：尾部无换行的末元素=写手中半行（或尾随空串），均不入帧。"""
    if not text:
        return []
    lines = text.split("\n")
    lines.pop()
    return lines


def frame(lineno, payload):
    """SSE 帧：id 游标（行号）+ data JSON 载荷 + 空行分隔。"""
    return "id: %d\ndata: %s\n\n" % (
        lineno, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def events(path, start_tail=0, poll_interval=DEFAULT_POLL_S, stop=None,
           keepalive_s=DEFAULT_KEEPALIVE_S):
    """追尾生成器。start_tail>0 吐尾部 min(start_tail, 总行数) 条；0=不吐存量。
    stop() 返回 True 即收尾（服务停机/连接废弃）；每次轮询后 sleep 让出。"""
    ka_polls = max(1, int(keepalive_s / poll_interval)) if poll_interval > 0 else 1
    cursor, idle, burst_done = 0, 0, False
    while True:
        lines = _complete_lines(_read_text(path))
        total = len(lines)
        if not burst_done:
            start = max(0, total - start_tail) if start_tail else total
            burst_done = True
        else:
            start = cursor
        for i in range(start, total):
            yield frame(i + 1, row_to_event(lines[i].split("\t")))
            cursor = i + 1
            idle = 0
        cursor = max(cursor, total)
        if stop is not None and stop():
            return
        idle += 1
        if idle >= ka_polls:
            yield ": keepalive\n\n"
            idle = 0
        time.sleep(poll_interval)
