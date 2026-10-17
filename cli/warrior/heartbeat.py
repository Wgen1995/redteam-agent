# -*- coding: utf-8 -*-
"""心跳与停滞（W5 战士 MVP）。

心跳=每 interval_min 分钟一条 timeline 心跳行（actor=warrior:<id>，
phase=P-lifecycle 基础设施轨，llmpool 先例）——进程活性的账本证据。
停滞=无进展超 stall_min → StallDetected（自杀重生信号：进程退出交租约
超时回收既有机制接管；重生日由 supervisor/操作员重启）。

钟源注入：now() → epoch 秒（FakeClock 可测）；iso_of() epoch→UTC Z 文本
（账本 ts 列口径）。
"""
import datetime

_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def iso_of(epoch):
    """epoch 秒 → UTC ISO8601 Z 文本（秒级，账本 ts 同口径）。"""
    return datetime.datetime.fromtimestamp(
        float(epoch), datetime.timezone.utc).strftime(_ISO_FMT)


class StallDetected(Exception):
    """停滞检出：无进展行超窗（携带 warrior/intent/空闲秒）。"""


class Heartbeat(object):
    """节流心跳 + 进展跟踪 + 停滞执法。"""

    def __init__(self, ledger_io, interval_min, stall_min, now):
        self.io = ledger_io
        self.interval_s = max(1.0, float(interval_min) * 60.0)
        self.stall_s = max(1.0, float(stall_min) * 60.0)
        self._now = now
        self._last_beat = None
        self._last_progress = float(now())

    def beat(self, intent="", extra=""):
        """节流心跳：距上次心跳 ≥ interval 才落行。返回是否落行。"""
        t = float(self._now())
        if self._last_beat is not None \
                and t - self._last_beat < self.interval_s:
            return False
        self._last_beat = t
        ev = "warrior-heartbeat warrior=%s" % self.io.warrior_id
        if intent:
            ev += " intent=" + intent
        if extra:
            ev += " " + str(extra)
        self.io.add_tl(ev, iso_of(t), phase="P-lifecycle")
        return True

    def progress(self):
        """进展行时间戳推进（工具执行/写账/意图迁移皆算进展）。"""
        self._last_progress = float(self._now())

    def check_stall(self, intent=""):
        idle = float(self._now()) - self._last_progress
        if idle > self.stall_s:
            raise StallDetected(
                "warrior=%s intent=%s 空闲 %ds 超停滞窗 %.0fmin"
                % (self.io.warrior_id, intent, int(idle),
                   self.stall_s / 60.0))
