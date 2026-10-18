# -*- coding: utf-8 -*-
"""两段判定+重复拒绝退避（CH exts/guardrail 吸收件①，E 舰 2026-10-19）。

源头（.research/repos/cyber-harness/exts/guardrail/runtime.go 只读参考）：
- 两段判定 Admit：risk=evaluate(check) → risk 非放行且 auto 档 →
  consequence=evaluate(confirm)（runtime.go:120-126）；后果明确无害才放行
  （REVIEW_REVIEW_STATE_APPROVED，runtime.go:141-153）。
- 判定失败=fail-closed：evaluate 出错/坏决策 → BLOCK "policy unavailable"
  （runtime.go:127-130,69-72），且失败判定不许被人审翻案（:155-157）——
  「不许跳过判定跑」的机械保证。
- 重复拒绝退避 repeatedRejection：（会话,回合,工具,参数规范串）sha256
  计数，第 2 次起 250ms×min(n-1,8) 递增等待+「勿重复同调用」提示回模型，
  计数面 1024 帽（runtime.go:162-178,206-230）。

战士化差异（对 diff 负责，逐条可查；总纲=
docs/reviews/2026-10-19-E-cyberharness-全件对齐.md §四.1/N3/N7）：
- 比它多的两层：①范围执法前置——判定前先过 scope（ledger.enforce 单源
  load_scope/out_of_scope_hosts；CH guardrail 只判风险不判范围），界外
  目标连判定器都不跑；②判定事件入链——两段各落一行 timeline（哈希链，
  第三方可验；CH 只进进程内事件流）。
- 退避键=（意图,卡,参数串）——CH 键到（会话,回合），回合结束即失效；
  我们一意图一脑（R1），同参刷门跨回合持续计数；且加第三档：同参拒绝
  达 max_rejects 次 → 该意图内该卡整卡停用（防死循环烧预算——被俘
  战士刷门在 CH 只会越来越慢，在这里直接断流）。
- fail-closed 拒绝也计退避（CH fail-closed 早退不计数）——判定服务
  持续坏时同样在烧回合预算，照计照停。
- 判定器=可注入函数 check_fn/confirm_fn: (card,args)->Decision——默认=
  机械规则表（宪法#43：机械判据优先于 LLM 自评；LLM 语义判定器=W2 G3
  ask 三态接线，届时注入即用，本件零改动）。人审档（CH safe/5min 超时）
  不在本件——ask 三态归 W2 G3。
- 永不 raise：任何内部异常都折叠成 fail-closed 拒绝（门律：坏门=关门，
  不是拆门）。

跑法：python3 -m unittest tests.test_warrior_guardrail -v
"""
import hashlib
import threading
import time
from collections import OrderedDict

__all__ = ["Decision", "Admission", "Guardrail", "NO_JUDGE",
           "default_check", "default_confirm", "default_scope_fn",
           "default_guardrail"]

RECORD = "record"   # 放行并留痕（CH Action_ACTION_RECORD）
BLOCK = "block"     # 拒（CH Action_ACTION_BLOCK）
_MAX_EV = 160       # 事件行 reason 截断（guard-reject 同量级）

# 默认机械规则表（风险文本/后果文本同源一条）：子串命中 joined 参数即亮灯。
# 表小而真：只收不可逆/停机级破坏形态；LLM 语义档=W2 G3 注入位。
_DESTRUCTIVE = (
    ("rm -rf", "参数带递归强删（rm -rf），删除不可逆",
     "会不可逆删除文件系统内容，目标数据无法找回"),
    ("rm -fr", "参数带递归强删（rm -fr），删除不可逆",
     "会不可逆删除文件系统内容，目标数据无法找回"),
    ("mkfs", "参数带磁盘重格式化（mkfs）",
     "会重写目标磁盘，分区与数据全毁"),
    ("drop table", "参数带 DROP TABLE 破坏性 SQL",
     "会删掉数据库整表，业务数据丢失"),
    ("drop database", "参数带 DROP DATABASE 破坏性 SQL",
     "会删掉整个数据库，业务停摆"),
    ("truncate table", "参数带 TRUNCATE 破坏性 SQL",
     "会清空数据库表数据"),
    ("shutdown", "参数带停机指令（shutdown）",
     "会关停目标主机，业务中断"),
    ("reboot", "参数带重启指令（reboot）",
     "会重启目标主机，业务中断"),
    (":(){ :|:& };:", "参数带 fork 炸弹",
     "会耗尽目标进程资源导致宕机"),
)


class _NoJudgeType(object):
    """显式「该段无判定器」哨兵（区别 None=用默认机械表）。"""

    def __call__(self, card, args):
        raise AssertionError("该段判定器未配置，不该被调用")


NO_JUDGE = _NoJudgeType()


class Decision(object):
    """一段判定的结论：action=record(放行)/block(拒) + 人话理由。"""

    __slots__ = ("action", "reason")

    def __init__(self, action, reason=""):
        self.action = action
        self.reason = str(reason or "")


class Admission(object):
    """admit() 的裁决面。

    stage ∈ ok(放行) / scope(范围前置拒) / risk(风险拒·无后果判定器时) /
    consequence(后果拒) / fail-closed(判定失败拒) / barred(意图内停卡拒)。
    """

    __slots__ = ("allowed", "stage", "reason", "attempts", "backoff_ms")

    def __init__(self, allowed, stage, reason, attempts=0, backoff_ms=0):
        self.allowed = allowed
        self.stage = stage
        self.reason = reason
        self.attempts = attempts
        self.backoff_ms = backoff_ms


def _flat(s, n=_MAX_EV):
    return " ".join(str(s).split())[:n]


def _valid(d):
    return isinstance(d, Decision) and d.action in (RECORD, BLOCK)


def _deny_reason(base, attempts):
    return ("%s（同样的调用已被拒 %d 次）。不要再用同样的参数重复这个"
            "调用：换参数、换工具，或说明受限之处。"
            % (base, attempts))


def default_check(card, args):
    """默认风险判定器（机械表）：这事危险吗。"""
    joined = " ".join(str(a) for a in args).lower()
    for pat, risk, _why in _DESTRUCTIVE:
        if pat in joined:
            return Decision(BLOCK, risk)
    return Decision(RECORD, "机械风险表无命中")


def default_confirm(card, args):
    """默认后果判定器（机械表）：会坏什么。"""
    joined = " ".join(str(a) for a in args).lower()
    for pat, _risk, why in _DESTRUCTIVE:
        if pat in joined:
            return Decision(BLOCK, why)
    return Decision(RECORD, "机械后果表无命中（后果不明不阻断，留痕）")


def default_scope_fn(io):
    """默认范围执法面：ledger.enforce 单源（scope.tsv 生效链）。

    返回 (ok, reason)：界外/排除/带主机而 scope.tsv 缺席=拒（fail-closed
    同 guard 律）；读账异常=拒。不带主机的调用不在此门（口径同
    out_of_scope_hosts）。
    """
    from ledger import core as ledger_core
    from ledger import enforce as ledger_enforce

    def scope(card, args):
        try:
            session = ledger_core.Session(io.goal_dir)
            scope_sets = ledger_enforce.load_scope(session)
            argv = [str(card)] + [str(a) for a in args]
            oob = ledger_enforce.out_of_scope_hosts(argv, scope_sets)
        except Exception as e:              # noqa: BLE001 —— 读账坏=关门
            return False, "范围账不可读（fail-closed）: %s" % _flat(e, 80)
        if oob:
            why = "、".join("%s(%s)" % (h, v) for h, v in oob[:4])
            return False, "目标不在作战范围内: %s" % why
        return True, ""
    return scope


class Guardrail(object):
    """一意图一脑的两段判定+退避运行时（loop 侧最小接线面）。

    用法：loop 在每条 tool 指令执行前 admit(card,args,iid,turn,ts)；
    allowed=False 即拒执行（reason 已含人话提示，直接回模型面）。
    意图切换零成本：退避键/停卡键都内嵌 iid，天然意图隔离。
    """

    def __init__(self, io, check_fn=None, confirm_fn=None, scope_fn=None,
                 max_rejects=3, base_ms=250, wait_cap=8, map_cap=1024,
                 sleeper=None):
        self.io = io
        self.check_fn = check_fn if check_fn is not None else default_check
        self.confirm_fn = (confirm_fn if confirm_fn is not None
                           else default_confirm)
        self.scope_fn = (scope_fn if scope_fn is not None
                         else default_scope_fn(io))
        self.max_rejects = max(1, int(max_rejects))
        self.base_ms = int(base_ms)
        self.wait_cap = int(wait_cap)
        self.map_cap = max(1, int(map_cap))
        self._sleep = sleeper if sleeper is not None else time.sleep
        self._rejections = OrderedDict()    # sha256(iid,card,args) → n
        self._barred = {}                   # (iid, card) → 触发帽计数
        self._mu = threading.Lock()         # 并行工具批下 admit 线程安全

    # ---- 内部面 ----

    def _ev(self, event, ts):
        try:
            self.io.add_tl(event, ts)
        except Exception:                  # noqa: BLE001 —— 入账失败不洗白裁决
            pass

    def _key(self, iid, card, args):
        joined = " ".join(str(a) for a in args)
        raw = "%s\x00%s\x00%s" % (iid, card, joined)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def rejection_keys(self):
        """退避计数键快照（计数面有帽的观测口）。"""
        return list(self._rejections.keys())

    def _count_rejection(self, iid, card, args):
        """同参拒绝计数（+1 返回新值）；计数面 FIFO 淘汰保帽。"""
        k = self._key(iid, card, args)
        if k not in self._rejections and len(self._rejections) >= self.map_cap:
            self._rejections.popitem(last=False)
        self._rejections[k] = self._rejections.get(k, 0) + 1
        return self._rejections[k]

    def _deny(self, stage, base_reason, iid, card, args, turn, ts):
        """拒面统一走：计数 → 停卡落账 → 递增等待 → 人话理由+提示。

        停卡语义：第 N 次拒绝（N=max_rejects）本身仍带判定段 stage
        （barred=1 旗记停卡生效），第 N+1 次起走 _admit 步 0 秒拒。
        """
        attempts = self._count_rejection(iid, card, args)
        engaged = attempts >= self.max_rejects
        if engaged:
            self._barred.setdefault((iid, card), attempts)
        backoff_ms = self.base_ms * min(attempts - 1, self.wait_cap)
        if backoff_ms > 0:
            self._sleep(backoff_ms / 1000.0)
        self._ev("guardrail-backoff intent=%s turn=%s card=%s attempts=%d "
                 "backoff_ms=%d%s"
                 % (iid, turn, card, attempts, backoff_ms,
                    " barred=1" if engaged else ""), ts)
        reason = base_reason
        if attempts >= 2:
            reason = _deny_reason(base_reason, attempts)
        if engaged:
            reason += ("%s 已达拒绝上限，这个意图内不再执行该卡："
                       "请改用其他工具或思路，确实受限就说明后结束。" % card)
        return Admission(False, stage, reason,
                         attempts=attempts, backoff_ms=backoff_ms)

    # ---- 主面 ----

    def admit(self, card, args, iid, turn="", ts=""):
        """tool 调用准入口。序：停卡 → 范围前置 → 风险段 → 后果段。

        永不 raise：内部异常折叠为 fail-closed 拒（不许跳过判定跑）。
        线程安全：同轮并行工具批（executor.py）下 admit 可并发——整程持
        锁（含退避等待：拒绝是罕见路，串行化代价可忽略，计数不丢不乱）。
        """
        try:
            with self._mu:
                return self._admit(card, args, iid, turn, ts)
        except Exception as e:              # noqa: BLE001 —— 坏门=关门
            return Admission(False, "fail-closed",
                             "判定通道异常，按 fail-closed 拒绝执行: %s"
                             % _flat(e, 120))

    def _admit(self, card, args, iid, turn, ts):
        # 0) 意图内停卡：最便宜最先，判定器都不再跑
        bar_at = self._barred.get((iid, card))
        if bar_at is not None:
            self._ev("guardrail-backoff intent=%s turn=%s card=%s "
                     "attempts=%d backoff_ms=0 barred=1"
                     % (iid, turn, card, bar_at), ts)
            return Admission(
                False, "barred",
                "%s 这个意图里已停止执行（同样的调用被拒 %d 次达到上限）。"
                "请改用其他工具或思路；确实受限就说明后结束。"
                % (card, bar_at), attempts=bar_at, backoff_ms=0)

        # 1) 范围执法前置（我们比 CH 多的层：判定前先过 scope）
        ok, sreason = self.scope_fn(card, args)
        if not ok:
            self._ev("guardrail-scope intent=%s turn=%s card=%s reason=%s"
                     % (iid, turn, card, _flat(sreason)), ts)
            return self._deny("scope", sreason, iid, card, args, turn, ts)

        # 2) 风险段：这事危险吗（永远入账）
        try:
            risk = self.check_fn(card, args)
            risk_ok = _valid(risk)
        except Exception as e:              # noqa: BLE001 —— 判定失败=fail-closed
            self._ev("guardrail-fail-closed intent=%s turn=%s card=%s "
                     "stage=risk error=%s" % (iid, turn, card, _flat(e)),
                     ts)
            return self._deny("fail-closed",
                              "判定服务失败，按 fail-closed 拒绝执行: %s"
                              % _flat(e), iid, card, args, turn, ts)
        if not risk_ok:
            self._ev("guardrail-fail-closed intent=%s turn=%s card=%s "
                     "stage=risk error=%s"
                     % (iid, turn, card, "坏决策 %r" % (risk,)), ts)
            return self._deny("fail-closed",
                              "判定服务失败（坏决策），按 fail-closed 拒绝执行",
                              iid, card, args, turn, ts)
        self._ev("guardrail-risk intent=%s turn=%s card=%s action=%s "
                 "reason=%s" % (iid, turn, card, risk.action,
                                _flat(risk.reason)), ts)

        # 3) 风险放行=低风险动作，不烧后果段
        if risk.action == RECORD:
            return Admission(True, "ok", risk.reason)

        # 4) 后果段：会坏什么（风险亮灯才跑；两段都入账）
        if self.confirm_fn is NO_JUDGE:
            return self._deny("risk", risk.reason, iid, card, args,
                              turn, ts)
        try:
            cons = self.confirm_fn(card, args)
            cons_ok = _valid(cons)
        except Exception as e:              # noqa: BLE001 —— 判定失败=fail-closed
            self._ev("guardrail-fail-closed intent=%s turn=%s card=%s "
                     "stage=consequence error=%s" % (iid, turn, card,
                                                     _flat(e)), ts)
            return self._deny("fail-closed",
                              "判定服务失败，按 fail-closed 拒绝执行: %s"
                              % _flat(e), iid, card, args, turn, ts)
        if not cons_ok:
            self._ev("guardrail-fail-closed intent=%s turn=%s card=%s "
                     "stage=consequence error=%s"
                     % (iid, turn, card, "坏决策 %r" % (cons,)), ts)
            return self._deny("fail-closed",
                              "判定服务失败（坏决策），按 fail-closed 拒绝执行",
                              iid, card, args, turn, ts)
        self._ev("guardrail-consequence intent=%s turn=%s card=%s "
                 "action=%s reason=%s" % (iid, turn, card, cons.action,
                                          _flat(cons.reason)), ts)
        if cons.action == RECORD:
            # auto 档两段制：风险亮灯但后果明确无害=放行（审计两段已入链）
            return Admission(True, "ok", cons.reason)
        return self._deny("consequence", cons.reason, iid, card, args,
                          turn, ts)


def default_guardrail(io, **kw):
    """生产默认档：机械两段判定器+ledger scope 前置+标准退避参数。"""
    return Guardrail(io, **kw)
