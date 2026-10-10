# -*- coding: utf-8 -*-
"""看门狗纯函数面（b10 v0.3.5）——multica 级四机制的计算核。

runner 只做编排；本模块零依赖可单测：
  stall_grade   分级击杀（soft=观察事件 / hard=击杀）
  backoff_delay 重启指数退避（base*4^(n-1)，cap 封顶；n<=0 不受罚）
  read_directive 指令注入通道（控制文件 digest 变化才触发；效果语义=
                带补令续跑——账本在盘，kill+resume 等价 multica pending 捎带）
  next_tick     自适应节流监听（活跃期压到 floor 秒级，静默回 tick——
                macOS 无零依赖 FSEvents，诚实命名"自适应"而非"事件驱动"）
"""
import hashlib


def stall_grade(stall_sec, soft=180.0, hard=480.0):
    """停滞分级：<soft='ok'；>=soft='soft'（观察，不杀）；>=hard='hard'（击杀）。"""
    if stall_sec >= hard:
        return 'hard'
    if stall_sec >= soft:
        return 'soft'
    return 'ok'


def backoff_delay(restart_n, base=30.0, cap=480.0):
    """第 n 次重启前的退避秒数：base*4^(n-1) 封顶 cap；n<=0 → 0（首次不受罚）。"""
    if restart_n <= 0:
        return 0.0
    return min(base * (4 ** (restart_n - 1)), cap)


def read_directive(path, seen_digest):
    """读战中指令控制文件。

    返回 (text, digest)：文件缺失 → (None, None)；digest 与上次相同 → (None, seen)
    （不重复触发）；内容变化 → (新文本, 新digest)。"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError:
        return None, None
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    if seen_digest is not None and digest == seen_digest:
        return None, seen_digest
    return text, digest


def next_tick(active, tick=10.0, floor=1.0):
    """自适应监听间隔：活跃 → floor（秒级响应）；静默 → tick（省 CPU）。"""
    return floor if active else tick


# ------------------------------------------------ v0.5a（SRE/AI agent 会诊项）

def budget_usage(json_line):
    """budget-check 首行 JSON → (used, limit) dict；坏输入 → None。"""
    import json
    try:
        d = json.loads(json_line)
        goal = d["goal"]
        return dict(goal["used"]), dict(goal["limit"])
    except (ValueError, KeyError, TypeError):
        return None


def budget_state(used, limit, warn=0.8):
    """预算执法分级：任一维超限='over'；任一维>warn 比例='warn'；否则 'ok'。"""
    state = "ok"
    for k, cap in limit.items():
        u = used.get(k, 0.0)
        if not cap or cap <= 0:
            continue
        if u > cap:
            return "over"
        if u > cap * warn and state == "ok":
            state = "warn"
    return state


def is_logonly(log_grew, tl_grew):
    """LOGONLY-ALIVE 判定：log 在长而 timeline 不动=战士在账本外干活（照亮不击杀）。"""
    return log_grew and not tl_grew


def logonly_should_emit(already, logonly_sec, soft):
    """LOGONLY 事件每停滞回合只记一次，且持续 soft 阈值后才记。"""
    return (not already) and logonly_sec >= soft


def ask_question(path):
    """ask:human 通道：ask.md 在场且非空 → 问题文本；否则 None。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            t = f.read().strip()
    except OSError:
        return None
    return t or None


def wait_state(ask_pending, answered):
    """WAIT 态机：有问题未答='WAIT'（停表不停命）——其余='RUN'。"""
    return "WAIT" if (ask_pending and not answered) else "RUN"
