# -*- coding: utf-8 -*-
"""续跑驱动（dsh P0 采纳③，纯函数版）。

对照 docs/research/2026-10-20-dsh-orchestration-inventory.md A 表#6/§③/
§⑧-3；dsh 出处 dsh-goal-round-driver/lib/index.js:11-18,105-164（轮计
硬上限 :125-131；防幻觉续跑提示 :11-18）。我方停序（yield→stop→预算→
时间窗→停滞）是「停」，本件补「续」：停滞重生后**从哪续、续几轮、何时
判死**的状态机。

四相（dsh goal 四相映射）：
  armed    = 可续跑（轮次未竭+无卸臂停止标记+盘上有活）；
  disarmed = 停止信号/预算/时间窗类 warrior-stop 为末生命周期行——需总控
             显式重臂，不自动续（dsh 失败即 disarm 同哲学）；
  blocked  = 轮计达 max_goal_rounds 硬上限但盘上仍有活——block_code=
             round-limit（dsh :125-131 自动 block 同律）；
  complete = 盘上无活（无自己活租约+无可领意图）。

轮计单源=盘上 timeline 自方 warrior-start 行数（loop.run() 每次重生必落
此行）——重启/断电不重置轮计（dsh roundsStarted 持久化于会话日志的等价
物=我方账本即日志）。检查点=dsh 每轮前 sessions.flush() 的等价物=账本
写本就即时落盘（append_tl_locked fsync 律），无需另设 flush 步。

纯函数律：只读盘上账本（timeline/intents/tool-executions），产出续跑
指令包（下一步=中断点+轮次+防幻觉提示）不落盘不调 LLM。断点接管判定
需传 now_ts（租约到期钟比较；loop 侧有 _ts() 单源）。

接线位（等修复舰落舱后总控接 loop；loop.py 冻结中，本件零改）：
  loop.run() 的 StallDetected 分支/重生进程入口:
      d = resume_driver.build_resume_directive(
          goal_dir, warrior_id, now_ts=self._ts())
      if d.resume:        # prompt 注入 steers/facts_extra 续跑
          steers_pending = [d.prompt] + steers_pending
      elif d.block_code == "round-limit":   # 判死：不再重生
          self._stop("round-limit", d.prompt)

与 dsh goal-round-driver 对照差异声明：
  同=①四相+轮计硬上限（超限自动 block code=round-limit）；②续跑提示词
     明写「以当前盘上态为准，不要相信此前叙述」（:11-18 防幻觉哲学移植
     为「以盘上账本为准,别信战士自述」）；③失败/停止即 disarm，不静默
     重试；④每轮之间检查点（我方=账本 fsync 律，语义等价）。
  异=①dsh goal 态存会话日志事件（armed/disarmed 显式事件），我方无独立
     goal 存储——四相从盘上 lifecycle 行+租约态**推导**（账本即状态机，
     与「防篡改账本」资产同根）；②dsh 驱动器在代理 idle 时自动注入
     followup（同进程），我方产出指令包由接线方（重生进程）消费；
  ③dsh flush 失败即 disarm，我方无独立 flush 面（写本即检查点）。
"""
import re

from ledger.timeline import read_rows
from .ledger_io import LedgerIO
from .repair import EXECUTIONS_NAME, TERMINAL_STATUSES, read_executions

#: 轮计硬上限默认（可配；dsh maxGoalRounds 同为构造参数）
DEFAULT_MAX_GOAL_ROUNDS = 8

_LIFECYCLE_PREFIXES = ("warrior-start", "warrior-stop", "warrior-stall",
                       "warrior-yield")
#: 卸臂停止因（需总控显式重臂；自然收敛 max-intents/no-intents 不卸臂）
_DISARM_REASONS = ("stop-signal", "halt", "budget-cap", "time-window")
_ROUND_LIMIT_CODE = "round-limit"
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]")
_REASON_RE = re.compile(r"reason=([^ ]+)")


class ResumeDirective(object):
    """续跑指令包：下一步=中断点+轮次+防幻觉提示（纯数据）。

    resume=是否续跑；phase=armed/disarmed/blocked/complete；rounds_
    started/max_goal_rounds/rounds_remaining=轮计三件；breakpoint=
    {intent_id, mode(reclaim-lease|claim-new), last_event}；dangling=
    断点意图的悬空执行 id；prompt=<goal_round> 指令文本；block_code/
    disarm_reason=判死/卸臂归因。
    """

    __slots__ = ("resume", "phase", "rounds_started", "max_goal_rounds",
                 "rounds_remaining", "breakpoint", "dangling", "prompt",
                 "block_code", "disarm_reason")

    def __init__(self, resume, phase, rounds_started, max_goal_rounds,
                 rounds_remaining, breakpoint, dangling, prompt,
                 block_code, disarm_reason):
        self.resume = bool(resume)
        self.phase = phase
        self.rounds_started = rounds_started
        self.max_goal_rounds = max_goal_rounds
        self.rounds_remaining = rounds_remaining
        self.breakpoint = breakpoint
        self.dangling = list(dangling)
        self.prompt = prompt
        self.block_code = block_code
        self.disarm_reason = disarm_reason


def _flat(s, n=200):
    return " ".join(str(s).split())[:n]


def _lifecycle_rows(timeline_rows, warrior_id):
    return [r for r in timeline_rows
            if len(r) > 3 and r[1] == warrior_id
            and r[3].startswith(_LIFECYCLE_PREFIXES)]


def _last_event_for(timeline_rows, iid):
    for r in reversed(timeline_rows):
        if len(r) > 3 and iid and iid in r[3]:
            return _flat(r[3])
    return ""


def _dangling_for(goal_dir, iid):
    """断点意图的悬空执行（running 无终态；id 前缀=EX-<safe(iid)>-t）。"""
    prefix = "EX-%s-t" % _SAFE_ID_RE.sub("_", str(iid))
    return [r["execution_id"] for r in read_executions(goal_dir)
            if r["status"] not in TERMINAL_STATUSES
            and r["execution_id"].startswith(prefix)]


def _prompt(rounds, max_rounds, bp, dangling):
    iid = bp.get("intent_id") or "?"
    mode = {"reclaim-lease": "接管自己活租约",
            "claim-new": "重新认领"}.get(bp.get("mode"), bp.get("mode"))
    if dangling:
        hang = "%s(结果未知,仅幂等才重试,有副作用先验证外部状态)" % (
            ",".join(dangling))
    else:
        hang = "无悬空"
    return ("<goal_round> 续跑第 %d/%d 轮。断点: intent=%s(%s); "
            "末事件: %s。铁律: 以盘上账本为准"
            "(timeline.tsv/facts.tsv/%s)，别信战士自述。"
            "悬空执行: %s。轮计=盘上 warrior-start 行数(%d)，重启不重置。"
            % (rounds, max_rounds, iid, mode,
               bp.get("last_event") or "(无)", EXECUTIONS_NAME, hang,
               rounds))


def build_resume_directive(goal_dir, warrior_id,
                           max_goal_rounds=DEFAULT_MAX_GOAL_ROUNDS,
                           now_ts=None):
    """盘上账本 → 续跑指令包（纯读，零写零调用）。

    断点优先序=接管自己活租约（reclaim-lease）＞重新认领可领意图
    （claim-new）；无活=complete。悬空执行只列断点意图的（精确归位，
    修复计划另行全量对账——见 repair.plan_repair 接线位）。
    """
    io = LedgerIO(goal_dir, warrior_id)      # 读面消费（零写方法）
    timeline_rows = read_rows(goal_dir)
    life = _lifecycle_rows(timeline_rows, warrior_id)
    rounds = sum(1 for r in life if r[3].startswith("warrior-start"))
    max_rounds = max(1, int(max_goal_rounds))
    active = io.my_active_intents(now_ts or "")
    claimable = io.claimable_intents()
    work = active or claimable

    if not work:
        bp = {"intent_id": "", "mode": "", "last_event": ""}
        return ResumeDirective(
            False, "complete", rounds, max_rounds,
            max(0, max_rounds - rounds), bp, [], "", "", "")
    if rounds >= max_rounds:
        bp = _breakpoint(active, claimable, timeline_rows)
        return ResumeDirective(
            False, "blocked", rounds, max_rounds, 0, bp,
            _dangling_for(goal_dir, bp["intent_id"]),
            "轮计 %d≥%d 达硬上限——round-limit 判死，不再重生"
            % (rounds, max_rounds),
            _ROUND_LIMIT_CODE, "")
    disarm_reason = ""
    if life:
        last = life[-1][3]
        if last.startswith("warrior-stop"):
            m = _REASON_RE.search(last)
            reason = m.group(1) if m else ""
            if reason in _DISARM_REASONS:
                disarm_reason = reason
    if disarm_reason:
        bp = _breakpoint(active, claimable, timeline_rows)
        return ResumeDirective(
            False, "disarmed", rounds, max_rounds,
            max(0, max_rounds - rounds), bp,
            _dangling_for(goal_dir, bp["intent_id"]),
            "末停止因 reason=%s 需总控显式重臂" % disarm_reason,
            "", disarm_reason)
    bp = _breakpoint(active, claimable, timeline_rows)
    dangling = _dangling_for(goal_dir, bp["intent_id"])
    prompt = _prompt(rounds, max_rounds, bp, dangling)
    return ResumeDirective(
        True, "armed", rounds, max_rounds,
        max(0, max_rounds - rounds), bp, dangling, prompt, "", "")


def _breakpoint(active, claimable, timeline_rows):
    if active:
        iid = active[0]["id"]
        mode = "reclaim-lease"
    elif claimable:
        iid = claimable[0]["id"]
        mode = "claim-new"
    else:
        iid, mode = "", ""
    return {"intent_id": iid, "mode": mode,
            "last_event": _last_event_for(timeline_rows, iid)}
