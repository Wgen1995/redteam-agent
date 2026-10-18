# -*- coding: utf-8 -*-
"""战士核心循环（W5 战士 MVP）。

ARTEX 角色铁律移植：领一意图→真工具执行→写事实→停（不开新方向）。
链路：领意图（intents 租约既有执法，--owner=warrior:<id>）→ 组上下文
（R1 一意图一脑：SKILL.md 协议原样+意图行+相关 facts+断点续跑末行+纠正
信号+定向指令）→ llmpool 选道调模型（通道选择/错误分类/冷却/429 切道）
→ 解析 JSON 指令块 → executor 同轮批执行（E舰③：无依赖 tool 并行
≤16+同卡同目标串行+账写原序屏障+结果按调用 id 归位，见 executor.py）→
tool 经 tools.gate.execute（卡层门链+guard 委托，
零复制）/ ledger 经 registry.lookup（goal 锁既有执法链，权面 allowlist）
→ 结果写账（facts=模型指令/timeline=进展行/transcript=R4 留痕/budget=
token 计量）→ done 释放 → 下一意图。

停序（每回合序）：让位（租约被抢）→ stop 信号（R5）→ 预算帽 → 时间窗
→ 停滞（无进展超窗→自杀重生：交租约超时回收，不擅自迁移意图状态）。
收敛：无可领意图（claimable ∅ 且无自己活租约）即停。

R2 串行链：done 后若存在 [prereq:本意图] 的 candidate 后继 → 恰提升
下一个后继进 pending（TodoStore 逐轮派发，不前置倾倒）。

接线四件（修复舰落舱后总控接线；各纯函数模块头注接线位单源）：
  ① repair        run() 落 warrior-start 行后 plan_repair 对账悬空执行
                  （合成收尾事件入 timeline + 状态行池同律原子重写）；
  ② compaction    process_intent 每 turn ctx.build 后 needs_compaction→                  build_compaction（summarizer=None 确定性抽取）产包替换
                  被遮蔽素材——上下文超限从终态变可恢复态；
  ③ resume_driver run() 重生入口 build_resume_directive：resume→prompt
                  注入 steers 续跑；round-limit→_stop 判死不再重生；
  ④ corps         __init__ 装配 load_corps + 领单后 resolve 出 skill_path
                  进简报 + tool/ledger 指令前置 authorize 拒=rc1+reason。
四线降级律：各模块缺席/无解/护栏拒=回退接线前行为（金样零漂移）。
"""
import os
import time

from . import compaction, corps, protocol, repair, resume_driver, steer
from .corrections import CorrectionLayer
from .budget import BudgetMeter
from .context import ContextBuilder
from .executor import MAX_PARALLEL_TOOLS, ToolBatchExecutor, flat as _flat
from .guardrail import default_guardrail
from .heartbeat import Heartbeat, StallDetected, iso_of
from .ledger_io import LedgerIO
from .model_client import ModelClient
from .transcript import Transcript


class RunReport(object):
    """一次 run() 的战报：status/stop_detail/processed/done_count/
    yielded_count/tokens_used/turns。"""

    __slots__ = ("status", "stop_detail", "processed", "done_count",
                 "yielded_count", "tokens_used", "turns")

    def __init__(self):
        self.status = ""
        self.stop_detail = ""
        self.processed = 0
        self.done_count = 0
        self.yielded_count = 0
        self.tokens_used = 0
        self.turns = 0


def _rewrite_executions(goal_dir, rows):
    """接线①：按 AsyncExecPool._persist 同律原子重写 tool-executions.tsv
    （tmp-pid 临时文件 + os.replace；executor.py:327 单源同形——树冻结期
    由总控接线落此行，不复制池实现只复刻落盘律）。"""
    path = os.path.join(goal_dir, repair.EXECUTIONS_NAME)
    tmp = "%s.tmp-%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("\t".join(str(r.get(k) or "")
                               for k in repair.EXECUTION_FIELDS) + "\n")
    os.replace(tmp, path)


class WarriorLoop(object):
    """一进程一循环；run() 同步执至停条件；dry_run() 零写零调。"""

    def __init__(self, goal_dir, battle_name, channels, pool,
                 warrior_id="warrior:W-1", max_intents=1, max_turns=6,
                 lease_min=30, token_cap=100000, time_window_min=None,
                 heartbeat_min=5.0, stall_min=15.0, ctx_tokens=24000,
                 skill_path=None, clock=None, tool_spawn=None,
                 tool_state_path=None, kb=True,
                 max_parallel_tools=MAX_PARALLEL_TOOLS,
                 guardrail=None, max_goal_rounds=None):
        self.battle = battle_name
        self.io = LedgerIO(goal_dir, warrior_id)
        self.warrior_id = warrior_id
        self.max_intents = max(1, int(max_intents))
        self.max_turns = max(1, int(max_turns))
        self.lease_min = max(1, int(lease_min))
        self.time_window_min = time_window_min
        self.clock = clock if clock is not None else time.time
        self.client = ModelClient(channels, pool)
        self.meter = BudgetMeter(self.io, token_cap)
        self.hb = Heartbeat(self.io, heartbeat_min, stall_min, self.clock)
        self.ctx = ContextBuilder(goal_dir, skill_path=skill_path,
                                  ctx_tokens=ctx_tokens, kb=kb)
        self.tr = Transcript(goal_dir, battle=battle_name,
                             warrior=warrior_id)
        self.tool_spawn = tool_spawn
        self.tool_state_path = tool_state_path
        # 接线③：轮计硬上限（dsh maxGoalRounds 同型构造参数；轮计单源=
        # 盘上 timeline 自方 warrior-start 行数——重启不重置）
        self.max_goal_rounds = max(
            1, int(max_goal_rounds or resume_driver.DEFAULT_MAX_GOAL_ROUNDS))
        # 接线④：兵种运行时装配（corps.py 装配位）——corps.yaml/卡面坏=
        # 降级 corps_rt=None 走默认面（金样零漂移，不炸战士）
        try:
            self.corps_rt = corps.load_corps(goal_dir)
        except Exception:                              # noqa: BLE001
            self.corps_rt = None
        self._default_skill_path = self.ctx.skill_path
        self._intent_corps = None        # 接线④：当前意图兵种（指令前置执法域）
        self.guardrail = (guardrail if guardrail is not None else   # 件①
                          default_guardrail(self.io))
        self._gr_scope = ("", 0)               # 件①：本回合判定执法域
        self.executor = ToolBatchExecutor(      # E舰③+F22韧性三件+接线④
            tool_exec=self._guarded_tool_exec,
            ledger_write=self._corps_ledger_write,
            now=self.clock, ts=self._ts, add_tl=self.io.add_tl,
            warrior_id=warrior_id, max_parallel=max_parallel_tools,
            goal_dir=goal_dir)  # F22：goal_dir 注入=断路器/异步/spill 三件齐装
        self._steer_idx = 0
        self._pending_steers = []
        self._deadline = None
        self.report = RunReport()

    # ---- 钟与工具 ----

    def _ts(self):
        return iso_of(self.clock())

    def _guarded_tool_exec(self, card, args):
        """件① seam + 接线④兵种前置：tool 执行前兵种面 authorize→两段
        判定+重复退避（E 吸收件①；R-CORPS-2 执行器前置同形）。

        拒=rc1+人话理由（经 err 面回模型，gate-reject 同形，「未执行」
        打头=拦截类拒绝不计断路器败）；放行才落既有卡层门链。
        _gr_scope/_intent_corps 由 process_intent 每回合先钉（并行批
        worker 读固定值）。"""
        if self._intent_corps is not None:      # 接线④：兵种面越权前置
            adm = corps.authorize(self._intent_corps, card)
            if not adm.allowed:
                return 1, "", "未执行（兵种面越权: %s）" % adm.reason
        iid, turn = self._gr_scope
        adm = self.guardrail.admit(card, args, iid, turn, self._ts())
        if not adm.allowed:
            return 1, "", "未执行（判定拦截: %s）" % adm.reason
        return self._tool_exec(card, args)

    def _corps_ledger_write(self, cmd, args):
        """接线④：账本指令兵种面前置（corps.py 装配位注释同形）。

        拒=rc1+reason 回模型面（executor._exec_ledger 同律入账
        warrior-progress rc=1）；放行=既有 registry 写命令面零复制。
        战士自身管理写（claim/complete/block/promote）直走 io.write
        不经此门——门只拦模型指令。"""
        if self._intent_corps is not None:
            adm = corps.authorize(self._intent_corps, cmd)
            if not adm.allowed:
                return 1, "未执行（兵种面越权: %s）" % adm.reason
        return self.io.write(cmd, args)

    def _resolve_corps(self, intent):
        """接线④：领单后兵种解析（corps.resolve；[corps:X] 直读优先、
        kind 缺省路由次之）。无解（kind 空+无兵种位/authz-diff 无缺省
        路由/未知兵种位）或未装配=降级走默认面——R-CORPS-1 的 fail-loud
        在 resolve 自身，loop 面降级保既有非兵种意图照跑（金样零漂移）。"""
        if self.corps_rt is None:
            return None
        try:
            return self.corps_rt.resolve(intent)
        except corps.CorpsError:
            return None

    def _tool_exec(self, card, args):
        from tools import gate as tool_gate
        try:
            return tool_gate.execute(
                self.io.goal_dir, card, args, self._ts(),
                spawn=self.tool_spawn, state_path=self.tool_state_path)
        except Exception as e:                    # noqa: BLE001
            return 2, "", "tool 通道异常: %s" % e

    # ---- 停件 ----

    def _stop(self, status, detail, current_iid=None, block_reason=None):
        if current_iid and block_reason:
            self.io.block(current_iid, self._ts(), reason=block_reason)
        self.io.add_tl("warrior-stop warrior=%s reason=%s %s"
                       % (self.warrior_id, status, _flat(detail, 200)),
                       self._ts(), phase="P-lifecycle")
        self.report.status = status
        self.report.stop_detail = detail
        self.report.tokens_used = self.meter.used_tokens
        return self.report

    # ---- 单意图回合机 ----

    def _turn_prologue(self, iid):
        """回合前停序：让位→stop 信号→预算→时间窗→心跳→停滞。返回
        ('cont', None) 或 (status, block_reason)。"""
        if not self.io.holds(iid, self._ts()):
            owner, _exp = self.io.owner_of(iid)
            self.io.add_tl("warrior-yield warrior=%s intent=%s to=%s"
                           % (self.warrior_id, iid, owner or "?"),
                           self._ts())
            self.report.yielded_count += 1
            return "yielded", None
        st = steer.scan(self.io.goal_dir, self.warrior_id, self._steer_idx)
        self._steer_idx = st.seen_idx
        if st.steers:
            self._pending_steers.extend(st.steers)
        if st.stop_reason:
            return ("stop-signal",
                    "stop-signal: " + st.stop_reason)
        if self.meter.exhausted():
            return ("budget-cap",
                    "budget-cap: used=%d cap=%d"
                    % (self.meter.used_tokens, self.meter.token_cap))
        if self._deadline is not None and self.clock() > self._deadline:
            return ("time-window",
                    "time-window: %.0fmin 窗尽"
                    % float(self.time_window_min))
        self.hb.beat(intent=iid,
                     extra="tokens=%d" % self.meter.used_tokens)
        self.hb.check_stall(intent=iid)
        return "cont", None

    def process_intent(self, intent, steers_pending):
        """一意图回合机：返回 ('done'|'yielded'|'blocked'|status, detail)。
        R1：conversation 仅本意图内累积，意图间零继承。"""
        iid = intent["id"]
        # 接线④：领单后兵种解析——卡面入简报（ContextBuilder 的
        # skill_path 注入位：兵种卡=本意图协议节）+ 指令前置执法域
        self._intent_corps = self._resolve_corps(intent)
        self.ctx.skill_path = (
            self._intent_corps.skill_path if self._intent_corps is not None
            else self._default_skill_path)
        conversation = []
        corrections = []
        corr = CorrectionLayer()                   # 一意图一层（R1）
        steers = list(steers_pending)
        steers_pending = []
        for turn in range(1, self.max_turns + 1):
            status, block_reason = self._turn_prologue(iid)
            if status != "cont":
                return status, block_reason
            if self._pending_steers:      # R5：回合间新到定向指令并入
                steers = steers + self._pending_steers
                self._pending_steers = []
            ctx = self.ctx.build(intent, corrections=corrections,
                                 steers=steers,
                                 facts_extra=corr.pinned_fact_lines())
            # 接线②：检查点压缩（dsh P0 采纳②；compaction.py 头注接线
            # 位）——ctx 超窗 → build_compaction 产包替换被遮蔽素材
            # （summarizer=None 确定性抽取，LLM 道留注入位）；未超窗/
            # 素材面未超（None）/护栏拒（CompactionRefused）=原文照发
            # （零漂移不炸回合——上下文超限从终态变可恢复态）
            brief = ctx.text
            if compaction.needs_compaction(ctx.estimated_tokens,
                                           self.ctx.ctx_tokens):
                try:
                    pkg = compaction.build_compaction(
                        intent=ctx.sections["intent"],
                        briefing=ctx.sections["resume"],
                        facts=[ln for ln in
                               ctx.sections["facts"].split("\n") if ln],
                        timeline=[ln for ln in
                                  ctx.sections["resume"].split("\n")
                                  if ln],
                        window_tokens=self.ctx.ctx_tokens)
                except compaction.CompactionRefused:
                    pkg = None          # 护栏拒=原文照发（降级）
                if pkg is not None:     # 摘要+保留尾替换被遮蔽素材
                    brief = pkg.text + "\n" + "\n".join(pkg.retained_tail)
            messages = ([{"role": "user", "content": brief}]
                        + conversation)
            self.tr.record(iid, "user", brief, ts=self._ts(),
                           model=self._model_name(), turn=turn)
            reply = self.client.chat(messages)
            self.meter.charge(iid, reply.prompt_tokens,
                              reply.completion_tokens, self._ts(),
                              note="model=%s turn=%d" % (reply.model or "?",
                                                         turn))
            self.hb.progress()
            self.report.turns += 1
            self.tr.record(iid, "assistant", reply.content
                           if reply.ok else "(model-fail %s)" % reply.reason,
                           ts=self._ts(), model=reply.model, turn=turn,
                           usage={"prompt_tokens": reply.prompt_tokens,
                                  "completion_tokens":
                                      reply.completion_tokens})
            if not reply.ok:
                corrections.append("model-fail reason=%s attempts=%s"
                                   % (reply.reason,
                                      [a["outcome"] for a in
                                       reply.attempts]))
                conversation.append({"role": "assistant",
                                     "content": "(model-fail)"})
                conversation.append({"role": "user",
                                     "content": "模型通道失败(%s)，请重试或"
                                                "报 done。" % reply.reason})
                continue
            parsed = protocol.parse(reply.content)
            conversation.append({"role": "assistant",
                                 "content": reply.content})
            corrections = [c for c in corrections if not c.startswith(
                "model-fail")]        # 通道恢复即清模型类纠正
            corrections += ["parse-error %s %s" % (e["error"], e["raw"])
                            for e in parsed.errors]
            if not parsed.instructions:
                conversation.append({"role": "user",
                                     "content": "未收到合法 JSON 指令块"
                                                "（%d 畸形）。请按协议输出。"
                                                % len(parsed.errors)})
                continue
            # E舰③：同轮指令批经并行执行器（三律+依赖律——见 executor.py；
            # 单 tool 回合行为与串行先例逐字节兼容）
            self._gr_scope = (iid, turn)   # 件①：判定执法域=本意图本回合
            batch = self.executor.execute(parsed.instructions, iid, turn,
                                          corr=corr)
            outcomes = batch.outcomes
            signals = batch.signals
            saw_done = batch.saw_done
            done_reason = batch.done_reason
            if outcomes:
                conversation.append({"role": "user",
                                     "content": "指令结果：\n" +
                                     "\n".join(outcomes)})
            if signals:
                corr.after_tool_batch(signals)
            corrections.extend(corr.take_hints())   # 次轮自纠信号
            if saw_done:
                ok, why = self.io.complete(iid, self._ts(),
                                           reason=done_reason)
                if ok:
                    self.report.done_count += 1
                    self.io.add_tl(
                        "warrior-progress warrior=%s intent=%s turn=%d "
                        "op=done reason=%s"
                        % (self.warrior_id, iid, turn,
                           _flat(done_reason, 120)), self._ts())
                    self._promote_chain_successor(iid)
                    self._planner_lazy_trigger()   # I-3①：收卡终态→规划者惰性触发
                    return "done", done_reason
                corrections.append("complete-fail %s" % why)
        return ("blocked",
                "max-turns: %d 回合未收敛" % self.max_turns)

    def _model_name(self):
        return (self.client.channels[0].get("model")
                or self.client.channels[0]["name"])

    def _promote_chain_successor(self, iid):
        """R2：恰提升下一个 [prereq:iid] candidate 后继进 pending。"""
        from ledger.write_cmds import _prereq_of
        for i in self.io.latest_intents():
            if i["status"] == "candidate" \
                    and _prereq_of(i.get("detail", "")) == iid:
                self.io.write("set-intent-status",
                              {"id": i["id"], "status": "pending",
                               "timestamp": self._ts()})
                return

    def _planner_lazy_trigger(self):
        """I-3① 接线（评审 I-3）：收卡终态→planner_loop.lazy_trigger。

        R-PLN-5 降级模式：规划者缺席合法，收卡方调即得与常驻轮同效的一轮
        （重派扫面+研判派活）；触发失败不阻战士（记 timeline 留痕即返）。
        """
        from ledger import planner_loop
        try:
            planner_loop.lazy_trigger(self.io.goal_dir, self._ts())
        except Exception as e:                    # noqa: BLE001
            self.io.add_tl("planner-lazy-fail warrior=%s %s"
                           % (self.warrior_id, _flat(e, 160)), self._ts(),
                           phase="P-lifecycle")

    # ---- 主入口 ----

    def run(self):
        # 接线③：续跑驱动（dsh P0 采纳③；resume_driver.py 头注接线位）——
        # 重生入口（停滞重生/断电重启同口）先于本世 warrior-start 判续/
        # 判死：轮计=盘上自方 warrior-start 行数（判死世不再落新 start=
        # 轮计封顶不漂）；账本撕裂等异常=降级直跑（后续自然执法面拦截）
        try:
            directive = resume_driver.build_resume_directive(
                self.io.goal_dir, self.warrior_id,
                max_goal_rounds=self.max_goal_rounds, now_ts=self._ts())
        except Exception:                              # noqa: BLE001
            directive = None
        steers_pending = []
        if directive is not None and directive.resume:
            steers_pending = [directive.prompt]   # prompt 注入 steers 续跑
        elif (directive is not None
                and directive.block_code == "round-limit"):
            return self._stop("round-limit", directive.prompt)  # 判死
        self.io.add_tl("warrior-start battle=%s warrior=%s pid=%s "
                       "channels=%d cap=%d"
                       % (self.battle, self.warrior_id, os.getpid(),
                          len(self.client.channels),
                          self.meter.token_cap), self._ts(),
                       phase="P-lifecycle")
        # 接线①：崩溃尾修复（dsh P0 采纳①；repair.py 头注接线位）——
        # 本世 warrior-start 行后对账悬空执行（他世崩溃遗留的 running
        # 行；池装载已对账的 orphaned 行不在修复面——单态源=盘上文件）：
        # 合成收尾事件入 timeline（ts=最后真实事件时戳，不假完成）+
        # 状态行升 orphaned-not-lost 按池同律原子重写；无悬空/已修过=
        # plan None 零漂移
        plan = repair.plan_repair(self.io.goal_dir)
        if plan is not None:
            self.io.add_tl(plan.timeline_event, plan.ts,
                           phase="P-lifecycle")
            _rewrite_executions(self.io.goal_dir, plan.repaired_rows)
        if self.time_window_min:
            self._deadline = self.clock() + float(self.time_window_min) * 60
        try:
            while self.report.processed < self.max_intents:
                st = steer.scan(self.io.goal_dir, self.warrior_id,
                                self._steer_idx)
                self._steer_idx = st.seen_idx
                if st.stop_reason:
                    return self._stop("stop-signal", st.stop_reason)
                if st.steers:
                    steers_pending = st.steers
                if self.meter.exhausted():
                    return self._stop(
                        "budget-cap",
                        "budget-cap: used=%d cap=%d"
                        % (self.meter.used_tokens,
                           self.meter.token_cap))
                if self._deadline is not None \
                        and self.clock() > self._deadline:
                    return self._stop("time-window",
                                      "time-window: %.0fmin 窗尽"
                                      % float(self.time_window_min))
                now = self._ts()
                mine = self.io.my_active_intents(now)
                if mine:
                    intent = mine[0]          # 断点续跑：接管自己活租约
                else:
                    cand = self.io.claimable_intents()
                    if not cand:
                        return self._stop(
                            "no-intents",
                            "无待领意图（pending/frontier 空）")
                    intent = cand[0]
                    ok, why = self.io.claim(intent["id"],
                                            lease_min=self.lease_min,
                                            ts=now)
                    if not ok:
                        continue      # 认领竞败（双抢互斥）：下一轮再选
                self.report.processed += 1
                status, detail = self.process_intent(intent,
                                                     steers_pending)
                # 接线④：意图收口即还原默认面（R1：意图间零继承）
                self._intent_corps = None
                self.ctx.skill_path = self._default_skill_path
                steers_pending = []
                if status == "done":
                    continue
                if status == "yielded":
                    continue
                # budget-cap / stop-signal / time-window / blocked(max-turns)
                if status in ("budget-cap", "stop-signal", "time-window"):
                    return self._stop(status, detail,
                                      current_iid=intent["id"],
                                      block_reason=detail.split(":")[0])
                if status == "blocked":
                    ok, why = self.io.block(intent["id"], self._ts(),
                                            reason="max-turns")
                    return self._stop("no-intents",
                                      "意图 %s max-turns 阻塞(%s)"
                                      % (intent["id"], why))
            return self._stop("max-intents",
                              "max-intents=%d 达限" % self.max_intents)
        except StallDetected as e:
            self.io.add_tl("warrior-stall warrior=%s detail=%s"
                           % (self.warrior_id, _flat(e, 200)), self._ts(),
                           phase="P-lifecycle")
            self.report.status = "stalled"
            self.report.stop_detail = str(e)
            self.report.tokens_used = self.meter.used_tokens
            return self.report

    def dry_run(self, limit=1):
        """只组上下文：不领、不写、不调模型。返回 ContextResult 列表。"""
        out = []
        for intent in self.io.claimable_intents()[:limit]:
            out.append(self.ctx.build(intent))
        return out
