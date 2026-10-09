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
