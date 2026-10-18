# -*- coding: utf-8 -*-
"""常驻规划者（功能5/8·补件二，设计 docs/design/2026-10-20-priority-planner-design.md）。

事件驱动派活闭环（W5）：timeline 行追加=事件 → 防抖窗（默认 800ms，可配，
ARTEX plannerLoop 同型）→ 触发=态势研判轮（可达空格×五因子排序公式 →
add_intent 走既有写入通道）+ 重派四分类扫面（补件三消费者接线）。
降级模式：收卡时惰性触发（规划者缺席合法，lazy_trigger 单发一轮同效）。

ARTEX 对照：它的事件=内存 notify 通道（丢了就丢）；我们=账本行，可回放可验真
（实时=回放特例律）。事件源=轮询令牌（watchdog.next_tick 自适应节流同款——
macOS 无零依赖 FSEvents，诚实命名"自适应轮询"）。

Ruling：
- R-PLN-1 事件源=change_token(epoch, timeline.tsv mtime_ns, size)：epoch 抓
  append_tl_locked 追加路径（.timeline.epoch 每次成功追加递增一世），mtime/size
  兜住 Ctx.commit 整表重写路径（写命令不递增 epoch）——两类写方都在账本上，
  令牌必变（timeline.py 只读复用，不改）。
- R-PLN-2 只派可达空格（P3 可达先行律公式化）：排序覆盖全部空格（不可达
  reach=0.3 只降序不派活——不可达收口走 unreachable: 置格通道，非派活），
  每轮至多 max_adds 张（防一轮倾倒）。
- R-PLN-3 派活走 registry.lookup("add-intent")（goal 写锁包装的既有执法链），
  不直接改 write_cmds（哨兵舰在改）；dedup_key=-+matrix-test+planner: 面 × 类
  机械判重=研判幂等；priority=五因子加权分（K1 通道回填，0-1 浮点硬门内）；
  detail 落五因子明细（可解释律：为什么它排第一，一眼懂）。
- R-PLN-4 防抖=ARTEX 形：首见变更起表（pending_since），窗内后续变更合并
  （drain，不起二表），now-pending_since≥窗长才触发；轮后令牌回基线（自写
  并入基线防自触发循环）。
- R-PLN-5 降级模式：lazy_trigger(goal_dir, ts) 无循环实例单发一轮（重派扫面+
  研判派活），与常驻轮同效——收卡方惰性触发，规划者缺席合法。
- R-PLN-6 轮询节奏=watchdog.next_tick 自适应（活跃期 floor 秒级/静默回 tick，
  in-machine 单源复用）；mono/sleep/ts_fn 全注入=测试确定性（零真实等待）。

写通道纪律：全部经 ledger.registry.lookup（既有执法链），不私铸 TSV 行。
"""
import contextlib
import io
import logging
import os
import time

from . import core, registry, replacer
from .planner_score import load_config, rank_gaps
from .query_cmds import _cell
from .timeline import _read_epoch
from .watchdog import next_tick

DEFAULT_POLL_TICK = 10.0   # 静默期轮询间隔（秒）
DEFAULT_POLL_FLOOR = 1.0   # 活跃期轮询间隔（秒）
REACH_YES = 1.0

_log = logging.getLogger("tanyin.planner")


def change_token(gd):
    """事件源令牌（R-PLN-1）：(epoch, timeline.tsv mtime_ns, size)。

    epoch=timeline._read_epoch（缺戳/损坏=0 世，宽容降读同源）；timeline.tsv
    缺失=(epoch, -1, -1)。两类写方（O(1) 追加/整表重写）都必动令牌。
    """
    epoch = _read_epoch(gd)
    try:
        st = os.stat(os.path.join(gd, "timeline.tsv"))
    except OSError:
        return (epoch, -1, -1)
    return (epoch, st.st_mtime_ns, st.st_size)


def should_fire(pending_since, now, debounce_ms):
    """防抖判定（纯函数，R-PLN-4）：pending_since 起表，now-起表≥窗长才触发。"""
    if pending_since is None:
        return False
    return (now - pending_since) * 1000.0 >= debounce_ms


# ---------------------------------------------------------------- 态势研判轮

def intent_title(surface, vclass):
    """规划者意图卡标题（dedup 稳定键的一部分）。"""
    return "planner: %s × %s" % (surface, vclass)


def _run(gd, cmd, args):
    """CLI 级既有入口（registry.lookup=goal 写锁包装执法链）。

    stdout+stderr 合并捕获（评审 I-1）：write_cmds._wrap 把 REJECT/用法
    错误写 stderr——只捕 stdout 则拒绝原因全空、且 "dedup_key" 竞速合并
    分支成死代码（空文本永不含关键字）；合并文本既带回原因又供竞速判定
    （warrior.ledger_io._run 同型）。
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = registry.lookup(cmd)(gd, list(args))
    return rc, buf.getvalue()


def _factor_detail(factors):
    return "planner 五因子 " + " ".join(
        "%s=%.4f" % (k, v) for k, v in factors.items())


def assess(goal_dir, ts, weights=None, max_adds=3, engine="web-blackbox"):
    """一轮态势研判（R-PLN-2/3）：可达空格×排序公式→add_intent 既有通道。

    返回本轮新派意图 [{title, priority, attack_surface, vuln_class}]；
    dedup_key 命中=跳过（幂等）；无空格/全已派=零写入零返回。
    """
    s = core.Session(goal_dir)
    ranked = rank_gaps(s, ts, weights=weights)
    existing = {_cell(r, "intents.tsv", "dedup_key")
                for r in s.rows("intents.tsv")}
    added = []
    for row in ranked:
        if len(added) >= max_adds:
            break
        if row["factors"]["reachability"] != REACH_YES:
            continue                      # R-PLN-2：只派可达空格
        surface, vclass = row["attack_surface"], row["vuln_class"]
        title = intent_title(surface, vclass)
        dedup = "-+matrix-test+" + title
        if dedup in existing:
            continue
        rc, out = _run(goal_dir, "add-intent", [
            "--title=" + title, "--detail=" + _factor_detail(row["factors"]),
            "--engine=" + engine, "--kind=matrix-test", "--origin=adjacency",
            "--budget-share=1;1;1", "--priority=%.4f" % row["score"],
            "--timestamp=" + ts])
        if rc == 0:
            existing.add(dedup)
            added.append({"title": title, "priority": "%.4f" % row["score"],
                          "attack_surface": surface, "vuln_class": vclass})
        elif "dedup_key" in out:
            continue                      # 并发战士竞速已派=合并（回放特例律）
        else:
            raise RuntimeError("规划者派活被拒: " + out)
    return added


def lazy_trigger(goal_dir, ts):
    """降级模式（R-PLN-5）：收卡时惰性触发单轮（重派扫面+研判派活）。

    规划者缺席合法：收卡方（战士运行时/看门狗）调本函数即得与常驻轮同效的
    一轮；配置（权重/max_adds/engine）读 goal 目录 planner.json。
    """
    cfg = load_config(goal_dir)
    replacer.sweep(goal_dir, ts)
    return assess(goal_dir, ts, weights=cfg["weights"],
                  max_adds=cfg["max_adds"], engine=cfg["engine"])


# ---------------------------------------------------------------- 常驻循环

class PlannerLoop(object):
    """常驻规划者：轮询令牌→防抖→研判轮。mono/sleep/ts_fn 全注入（R-PLN-6）。

    用法（生产）：
        PlannerLoop(goal_dir, ts_fn=<ISO 钟>).run()
    用法（测试）：FakeClock 注入 mono/sleep，poll() 单步驱动，断言状态机。
    """

    def __init__(self, goal_dir, ts_fn, mono=time.monotonic, sleep=time.sleep,
                 debounce_ms=None, poll_interval=None, weights=None,
                 max_adds=None, engine=None, poll_tick=DEFAULT_POLL_TICK,
                 poll_floor=DEFAULT_POLL_FLOOR):
        cfg = load_config(goal_dir)      # 配置坏=fail-loud 拒启（R-SCO-7）
        self.goal_dir = goal_dir
        self.ts_fn = ts_fn
        self.mono = mono
        self.sleep = sleep
        self.debounce_ms = debounce_ms if debounce_ms is not None \
            else cfg["debounce_ms"]
        self.poll_interval = poll_interval
        self.poll_tick = poll_tick
        self.poll_floor = poll_floor
        self.weights = weights if weights is not None else cfg["weights"]
        self.max_adds = max_adds if max_adds is not None else cfg["max_adds"]
        self.engine = engine if engine is not None else cfg["engine"]
        self.baseline = change_token(goal_dir)
        self.pending_since = None
        self.rounds = 0

    def _round(self):
        """一轮=重派扫面+态势研判（补件三消费者与补件二同轮接线）。"""
        ts = self.ts_fn()
        replacer.sweep(self.goal_dir, ts)
        added = assess(self.goal_dir, ts, weights=self.weights,
                       max_adds=self.max_adds, engine=self.engine)
        self.baseline = change_token(self.goal_dir)   # R-PLN-4：自写回基线
        self.pending_since = None
        self.rounds += 1
        return added

    def poll(self):
        """单步：读令牌→防抖判定→（过窗）研判轮。返回 idle/pending/fired。"""
        token = change_token(self.goal_dir)
        now = self.mono()
        if token != self.baseline and self.pending_since is None:
            self.pending_since = now      # ARTEX：首唤醒起表，窗内后续合并
        if should_fire(self.pending_since, now, self.debounce_ms):
            self._round()
            return "fired"
        if self.poll_interval is not None:
            self.sleep(self.poll_interval)   # 测试注入节奏（含活跃/静默同拍）
        else:
            self.sleep(next_tick(self.pending_since is not None,
                                 self.poll_tick, self.poll_floor))  # 生产自适应
        return "pending" if self.pending_since is not None else "idle"

    def run(self, max_rounds=None):
        """常驻主循环（max_rounds=None=常驻；测试可限轮防死循环）。

        兜底（评审 I-1）：单轮异常不杀常驻循环——异常经 append-timeline
        既有通道记事件入账本（可回放、带原因），失败轮也计轮（max_rounds
        必有界推进）并清防抖表+按静默拍休眠（防持续失败热循环），下轮
        重新武装照常服务。
        """
        while max_rounds is None or self.rounds < max_rounds:
            try:
                self.poll()
            except Exception as e:                  # noqa: BLE001
                self._record_round_failure(e)
                self.rounds += 1
                self.pending_since = None
                self.sleep(self.poll_tick)
        return self.rounds

    def _record_round_failure(self, exc):
        """单轮异常记事件（尽力而为：事件写失败只留日志，不杀循环）。"""
        reason = " ".join(str(exc).split())[:160]
        try:
            rc, out = _run(self.goal_dir, "append-timeline", [
                "--actor=子代理", "--phase=P3",
                "--event=planner-round-fail rounds=%d err=%s"
                % (self.rounds + 1, reason),
                "--timestamp=" + self.ts_fn()])
            if rc != 0:
                _log.warning("planner-round-fail 事件写失败 rc=%d: %s",
                             rc, out)
        except Exception:                           # noqa: BLE001
            _log.warning("planner-round-fail 事件写异常", exc_info=True)
