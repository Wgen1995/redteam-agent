# -*- coding: utf-8 -*-
"""同轮指令并行执行器（E 舰吸收件③：cyber-harness loop.go:498 语义对齐）
+F22 韧性三件（能力对照总账第一优先补件，2026-10-20 §F22）。

对齐档（docs/reviews/2026-10-19-E-cyberharness-全件对齐.md E3/N2 引
architecture.md:54+loop.go:498+defaults.go:15 成熟语义）三律+依赖律：
  律① 同轮无依赖 tool 并行——信号量上限 16（MAX_PARALLEL_TOOLS，
       defaults.go:15 同源默认），批内无隐式排序；
  律② 并行执行、串行入账——账本写保持派发原序（哈希链不乱）：ledger/
       note/done=批次屏障（等在飞批收拢后才动账），tool 的 warrior-progress
       事件按调用 id 原序串行补记；账本侧 flock（append_tl_locked→goal_lock）
       天然线程安全=对齐档既判，本层零改动；
  律③ 完成序与派发序解耦——结果按调用 id（指令派发序号）归位，模型看到的
       「指令结果」面恒为派发序，与完成序无关；
  律④ 保守依赖检测——同卡同目标串行（同资产读写不并行）：目标=argv 末位起
      首个含 . 或 : 的非旗标参数（CLI 卡目标位惯例），无目标相=同卡全串行
       （保守失败方向=多串行、不少并行）。

线程纪律：CorrectionLayer 与账本写非线程安全面全部留主线程——调前预检/
调后自纠/入账按派发序串行执行（自纠观察语义与串行执行逐字节一致）；
只有 tool_spawn（gate.execute→guard 子进程面）进工作线程。
截断响应不执行工具：协议层天然免疫（未闭合围栏不产指令）+model_client
finish_reason=length 弃答（reason=truncated）双层兜底，不在本层重复执法。

F22 韧性三件（goal_dir 注入即活；三件全部阈值可配、未触达时行为与
三件落地前逐字节一致——金样纪律「同输入同 execution 行为」）：
  件a 异步 execution_id——长任务（async_threshold_s，默认 60s）有界等待
       超时即转后台守护线程续跑，发卡回 execution_id（意图/轮/调用位
       确定性铸造），不占战士轮次不超时丢果；结果后续 execute() 自动
       回填（轮询续接）+poll_execution 可查；状态行落 goal 目录
       tool-executions.tsv 可回放，进程重启装载即孤儿对账（CSAI
       execution_service 同型：有界等待+get/wait 轮询续接，冲击#7）。
  件b 卡层断路器——连续 N 失败（默认 3）熔断该卡冷却（默认 15min，
       15/30/60min 长档），llmpool 分道冷却同型移植（连续计数→熔断→
       冷却窗→惰性到期→成功治愈→状态落盘→事件入账；判定拦截类拒绝
       =「未执行」打头，llmpool no_failover 同律不动计数）；状态原子
       落盘 tool-breaker.json，重启恢复未到期冷却窗。
  件c 超大输出 spill——输出超阈值（spill_threshold_bytes，默认 1MB）
       全文落盘 goal 目录 tmp/spill-<卡>-<内容哈希>.txt（同内容同路径
       幂等），模型上下文只进摘要+指针（防炸脑），全文留档可取回
       （不丢果）；自纠层仍吃原文（提取信号面不受 spill 影响）。
"""
import hashlib
import json
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from .corrections import correction_note

MAX_PARALLEL_TOOLS = 16        # 信号量上限（cyber-harness defaults.go:15 同源）
_UNPARSED_TARGET = "*"         # 目标不可辨：同卡全串行（保守）

# ---- F22 韧性三件阈值（全部可配：构造参数逐项覆盖；默认值=方案钉死值） ----
ASYNC_THRESHOLD_S = 60.0       # 件a：有界等待阈值（超时转后台发卡）
SPILL_THRESHOLD_BYTES = 1000000  # 件c：超大输出落盘阈值（1MB）
BREAKER_FAIL_THRESHOLD = 3     # 件b：连续 N 失败熔断
BREAKER_LADDER_S = (900.0, 1800.0, 3600.0)  # 件b：冷却长档 15/30/60min
BREAKER_JITTER = 0.2           # 件b：冷却 ±20% 抖动（llmpool 同型）
POLICY_DENIAL_PREFIX = "未执行"  # 判定/断路器拦截类拒绝前缀（不计败）
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]")


def flat(s, n=1500):
    """压空白+截断单行化（loop.py 原单源迁入，loop 同名引用零漂移）。"""
    return " ".join(str(s).split())[:n]


def target_of(args):
    """依赖键目标相：末位起首个「非旗标且含 . 或 :」参数（host/url/ip/
    端口位惯例，dig/curl/nmap/httpx 卡形皆中）；无→''。旗标值含点（如
    gobuster -w wordlist.txt）可能被抬为目标——抬错只多串行不少并行，
    保守方向可接受。"""
    for a in reversed(list(args or [])):
        s = str(a)
        if not s.startswith("-") and ("." in s or ":" in s):
            return s
    return ""


def dep_key(card, args):
    """律④保守依赖键：(卡, 目标)；目标不可辨=同卡全串行哨兵。"""
    t = target_of(args)
    return (str(card), t) if t else (str(card), _UNPARSED_TARGET)


def mint_execution_id(iid, turn, idx):
    """件a：execution_id 确定性铸造=EX-<意图>-t<轮>-c<调用位>（同输入同
    id，金样律）；iid 非安全字符压 _（账本行 id 形 IN-xxxx 天然安全）。"""
    return "EX-%s-t%d-c%d" % (_SAFE_ID_RE.sub("_", str(iid)),
                              int(turn), int(idx))


def spill_output(goal_dir, card, out, err, threshold=SPILL_THRESHOLD_BYTES):
    """件c：超大输出落盘（goal 目录 tmp/spill-<卡>-<内容哈希>.txt）。

    返回 (out_view, err_view, spill_path)：超阈值→全文幂等落盘+模型面只
    进「摘要+指针」；未超阈值/goal_dir 缺→原样返回（零行为漂移）。
    同内容同路径（sha256 前 16 位命名）——重跑同输出不重复占盘。
    """
    out, err = str(out), str(err)
    total = len(out) + len(err)
    if goal_dir is None or total <= int(threshold):
        return out, err, None
    body = out + (("\n[stderr]\n" + err) if err else "")
    digest = hashlib.sha256(body.encode("utf-8", "replace")).hexdigest()[:16]
    tmp_dir = os.path.join(goal_dir, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, "spill-%s-%s.txt" % (card, digest))
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    head, tail = body[:120], body[-120:]
    out_v = ("SPILL %dB>=%dB spill=%s 头120=%s…尾120=%s"
             % (total, int(threshold), path, head, tail))
    err_v = ("见同上 spill 文件 %s" % path) if len(err) > 4000 else err
    return out_v, err_v, path


class CardBreaker(object):
    """件b：卡层断路器（llmpool 分道冷却同型移植——不重造状态机形状）。

    分类（llmpool.classify no_failover 同律）：
      rc==0                       → ok：治愈（计数/熔断档全量清零）
      rc!=0 且 err「未执行」打头  → 判定/断路器拦截类拒绝：保守不动计数
      其余 rc!=0                  → 失败：连续计数 +1，达阈值熔断
    冷却：BREAKER_LADDER_S 按累计熔断次数取档（15/30/60min 封顶），
    ±20% 抖动（rng 注入可测）；冷却窗过=惰性恢复（保留档位计数防抖动
    复活）；成功 report 才全量清零。状态原子落盘（llmpool_state.json
    同律：corrupt=全新启动），重启恢复未到期冷却窗。
    事件（经注入 emit）：tool-breaker card=… event=trip|recover。
    """

    def __init__(self, state_path=None, now=None, rng=None,
                 fail_threshold=BREAKER_FAIL_THRESHOLD,
                 ladder=BREAKER_LADDER_S, emit=None):
        self.state_path = state_path
        self._now = now if now is not None else (lambda: 0.0)
        self._rng = rng if rng is not None else (lambda: 0.5)
        self.fail_threshold = max(1, int(fail_threshold))
        self.ladder = tuple(float(x) for x in ladder) or (900.0,)
        self._emit = emit
        self._states = {}
        self._load()

    # ---- 三面 ----

    def allows(self, card):
        """熔断判定 → (ok, reason)：冷却中=拒（人话剩余秒）；惰性到期
        就地恢复（发 recover 事件）。拒时 reason 以「未执行」打头（拦截
        类前缀——被拒调用不得再喂计数）。"""
        st = self._states.get(str(card))
        if st is None:
            return True, ""
        if st["cooldown_end"] > 0.0:
            if self._now() >= st["cooldown_end"]:
                st["cooldown_end"] = 0.0
                st["fail_streak"] = 0
                self._persist()
                self._fire(card, "recover", "cooldown-expired", 0)
                return True, ""
            remain = int(st["cooldown_end"] - self._now()) + 1
            return False, ("未执行（断路器冷却中: 卡%s 连续%d败熔断，"
                           "约%ds后自动恢复）" % (card, self.fail_threshold,
                                                  remain))
        return True, ""

    def report(self, card, rc, err=""):
        """上报单次执行结果 → None（快照面经 allows/状态文件可查）。"""
        card = str(card)
        if rc == 0:                                  # ok：成功治愈
            st = self._states.get(card)
            if st is not None and (st["cooldown_end"] > 0.0
                                   or st["fail_streak"]
                                   or st["trip_count"]):
                self._fire(card, "recover", "success", 0)
            self._states[card] = self._new_state(preserve_trips=False)
            self._persist()
            return
        if str(err).startswith(POLICY_DENIAL_PREFIX):
            return                                   # no_failover：不动计数
        st = self._states.setdefault(card, self._new_state())
        if st["cooldown_end"] > 0.0:                 # 冷却中不再累计（拒≠败）
            return
        st["fail_streak"] += 1
        if st["fail_streak"] >= self.fail_threshold:
            self._trip(card, st)
        self._persist()

    # ---- 内部 ----

    @staticmethod
    def _new_state(preserve_trips=True, trips=0):
        return {"fail_streak": 0, "trip_count": int(trips) if preserve_trips
                else 0, "cooldown_end": 0.0}

    def _trip(self, card, st):
        st["fail_streak"] = 0
        st["trip_count"] += 1
        base = self.ladder[min(st["trip_count"], len(self.ladder)) - 1]
        cooldown = base * (1.0 + BREAKER_JITTER * (2.0 * self._rng() - 1.0))
        st["cooldown_end"] = self._now() + cooldown
        self._fire(card, "trip", "consecutive-fails",
                   int(round(cooldown)))

    def _fire(self, card, event, reason, cooldown_s):
        if self._emit is None:
            return
        try:
            self._emit("tool-breaker card=%s event=%s reason=%s"
                       " cooldown_s=%d" % (card, event, reason, cooldown_s))
        except Exception:                            # noqa: BLE001
            pass                                     # 事件不炸判定

    def _persist(self):
        if not self.state_path:
            return
        try:
            d = os.path.dirname(os.path.abspath(self.state_path))
            os.makedirs(d, exist_ok=True)
            tmp = "%s.tmp-%d" % (self.state_path, os.getpid())
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                json.dump(self._states, f, ensure_ascii=False, sort_keys=True)
            os.replace(tmp, self.state_path)          # 原子换（llmpool 同律）
        except OSError:
            pass                                      # 落盘失败不炸执行

    def _load(self):
        if not self.state_path or not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, encoding="utf-8") as f:
                raw = json.load(f)
            for k, v in raw.items():
                if isinstance(v, dict):
                    self._states[str(k)] = {
                        "fail_streak": int(v.get("fail_streak", 0)),
                        "trip_count": int(v.get("trip_count", 0)),
                        "cooldown_end": float(v.get("cooldown_end", 0.0))}
        except (OSError, ValueError):
            self._states = {}                         # corrupt=全新启动


class AsyncExecPool(object):
    """件a：异步执行池（发卡即回 execution_id，后台守护线程续跑）。

    状态行落 goal 目录 tool-executions.tsv（七列：execution_id/card/
    status/submitted_ts/finished_ts/rc/spill_path，原子重写可回放）；
    装载时他进程遗留 running 行=孤儿对账（标 orphaned——不假完成不丢
    行，CSAI orphaned 同型）；completed/failed 行装载后未回填标记清零
    （重启后续轮补交，不丢果）。
    线程纪律：register/complete 持锁（后台线程可调，仅内存+落盘零账本
    写）；take_ready/poll/pending 主线程收拢。
    """

    FIELDS = ("execution_id", "card", "status", "submitted_ts",
              "finished_ts", "rc", "spill_path")

    def __init__(self, state_path=None, ts=None):
        self.state_path = state_path
        self._ts = ts if ts is not None else (lambda: "")
        self._lock = threading.Lock()
        self._rows = {}
        self._load()

    def register(self, execution_id, card, submitted_ts=None):
        """登记 running 行（同 id 在册未收拢→确定性 -r<N> 后缀防撞）。"""
        with self._lock:
            eid = execution_id
            n = 0
            while eid in self._rows and not self._rows[eid]["reaped"]:
                n += 1
                eid = "%s-r%d" % (execution_id, n)
            self._rows[eid] = {
                "execution_id": eid, "card": str(card), "status": "running",
                "rc": None, "out": "", "err": "", "spill_path": "",
                "submitted_ts": submitted_ts or self._ts(),
                "finished_ts": "", "reaped": False}
            self._persist()
            return eid

    def complete(self, execution_id, rc, out_v, err_v, spill_path,
                 finished_ts=None):
        """后台线程收口：completed/failed（rc!=0）+spill 视图入册。"""
        with self._lock:
            r = self._rows.get(execution_id)
            if r is None or r["status"] != "running":
                return
            r.update({"status": "completed" if rc == 0 else "failed",
                      "rc": rc, "out": out_v, "err": err_v,
                      "spill_path": spill_path or "",
                      "finished_ts": finished_ts or self._ts()})
            self._persist()

    def take_ready(self):
        """收拢已完成未回填行（主线程；回填后标 reaped 防重复交果）。"""
        with self._lock:
            ready = [dict(r) for r in self._rows.values()
                     if r["status"] in ("completed", "failed")
                     and not r["reaped"]]
            for r in self._rows.values():
                if r["status"] in ("completed", "failed") and not r["reaped"]:
                    r["reaped"] = True
            return ready

    def poll(self, execution_id):
        """单查快照（get_tool_execution 同型；未知 id=unknown）。"""
        with self._lock:
            r = self._rows.get(execution_id)
            if r is None:
                return {"execution_id": execution_id, "status": "unknown"}
            return {k: r[k] for k in ("execution_id", "card", "status",
                                      "rc", "out", "err", "spill_path",
                                      "submitted_ts", "finished_ts")}

    def pending(self):
        """未回填全量快照 {id: 同 poll 形}（wait/巡检面）。"""
        with self._lock:
            return {r["execution_id"]:
                    {k: r[k] for k in ("execution_id", "card", "status",
                                       "rc", "out", "err", "spill_path",
                                       "submitted_ts", "finished_ts")}
                    for r in self._rows.values() if not r["reaped"]}

    # ---- 内部 ----

    def _persist(self):
        if not self.state_path:
            return
        try:
            d = os.path.dirname(os.path.abspath(self.state_path))
            os.makedirs(d, exist_ok=True)
            tmp = "%s.tmp-%d" % (self.state_path, os.getpid())
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                for eid in sorted(self._rows):
                    r = self._rows[eid]
                    f.write("\t".join([
                        r["execution_id"], r["card"], r["status"],
                        r["submitted_ts"], r["finished_ts"],
                        "" if r["rc"] is None else str(r["rc"]),
                        r["spill_path"] or ""]) + "\n")
            os.replace(tmp, self.state_path)
        except OSError:
            pass

    def _load(self):
        if not self.state_path or not os.path.exists(self.state_path):
            return
        dirty = False
        try:
            with open(self.state_path, encoding="utf-8") as f:
                for ln in f:
                    parts = ln.rstrip("\n").split("\t")
                    if len(parts) != len(self.FIELDS):
                        continue
                    eid, card, status, sub, fin, rc, sp = parts
                    if eid in self._rows:
                        continue
                    if status == "running":            # 孤儿对账：不假完成
                        status = "orphaned"
                        dirty = True
                    self._rows[eid] = {
                        "execution_id": eid, "card": card, "status": status,
                        "rc": None if rc == "" else int(rc),
                        "out": "", "err": "", "spill_path": sp,
                        "submitted_ts": sub, "finished_ts": fin,
                        "reaped": status in ("orphaned",)}  # 孤儿不再交果
        except OSError:
            return
        if dirty:
            self._persist()


class BatchResult(object):
    """一轮指令批战果：outcomes（派发序 summary）/signals（派发序自纠
    信号）/saw_done/done_reason。"""

    __slots__ = ("outcomes", "signals", "saw_done", "done_reason")

    def __init__(self, outcomes, signals, saw_done, done_reason):
        self.outcomes = outcomes
        self.signals = signals
        self.saw_done = saw_done
        self.done_reason = done_reason


class ToolBatchExecutor(object):
    """同轮指令批执行器：连续 tool 段并行发批（律①④），ledger/note/done
    串行屏障（律②），结果按调用 id 归位（律③）。端口全注入
    （tool_exec/ledger_write/now/add_tl）——loop 装配、单测假件直挂。

    F22 韧性三件：goal_dir 注入即活（断路器/异步池/spill 三件齐装）；
    goal_dir 缺省=纯同步老路（既有直挂用法零漂移）。三件阈值全部构造
    可配；阈值未触达时 outcomes/事件行与三件前逐字节一致（金样律）。"""

    def __init__(self, tool_exec, ledger_write, now, ts, add_tl, warrior_id,
                 max_parallel=MAX_PARALLEL_TOOLS, goal_dir=None,
                 async_threshold_s=ASYNC_THRESHOLD_S,
                 spill_threshold_bytes=SPILL_THRESHOLD_BYTES,
                 breaker_fail_threshold=BREAKER_FAIL_THRESHOLD,
                 breaker_rng=None):
        """端口注入：now=浮点钟（时延计量）、ts=ISO 时戳铸造（入账面），
        add_tl=timeline 事件单源写方，ledger_write=registry 写命令面。
        goal_dir=F22 三件装配位（断路器/异步池状态与 spill 落此）。"""
        self._tool_exec = tool_exec
        self._ledger_write = ledger_write
        self._clock = now
        self._ts = ts
        self._add_tl = add_tl
        self._warrior = warrior_id
        self.max_parallel = max(1, int(max_parallel))
        self._goal_dir = goal_dir
        self._async_threshold_s = float(async_threshold_s or 0.0)
        self._spill_threshold = int(spill_threshold_bytes)
        self._breaker = (
            CardBreaker(state_path=os.path.join(goal_dir, "tool-breaker.json"),
                        now=now, rng=breaker_rng,
                        fail_threshold=breaker_fail_threshold,
                        emit=self._breaker_event)
            if goal_dir else None)
        self._async = (
            AsyncExecPool(state_path=os.path.join(
                goal_dir, "tool-executions.tsv"), ts=ts)
            if goal_dir else None)

    # ---- 主入口 ----

    def execute(self, instructions, iid, turn, corr=None):
        """指令列表（派发序）→ BatchResult。done 即止（其后指令不执行，
        与既有串行语义一致）；每条非 done 恰产一条 outcome（派发序）；
        件a：入口先收拢已完成异步行（回填 outcome 排最前，先交旧账）。"""
        outcomes = self._reap_async(iid, turn)
        signals = []
        i, n = 0, len(instructions)
        while i < n:
            ins = instructions[i]
            op = ins.get("op")
            if op == "tool":
                batch = []
                while i < n and instructions[i].get("op") == "tool":
                    batch.append((i, instructions[i]))
                    i += 1
                b_out, b_sig = self._run_tool_batch(batch, iid, turn, corr)
                outcomes.extend(b_out)
                signals.extend(b_sig)
                continue
            if op == "ledger":
                outcomes.append(self._exec_ledger(ins, iid, turn))
            elif op == "note":
                outcomes.append("note: " + flat(ins.get("text", ""), 200))
            elif op == "done":
                return BatchResult(outcomes, signals, True,
                                   ins.get("reason", ""))
            else:
                outcomes.append("unknown op")
            i += 1
        return BatchResult(outcomes, signals, False, "")

    # ---- 件a 轮询面 ----

    def poll_execution(self, execution_id):
        """单查异步执行（get_tool_execution 同型）：running/completed/
        failed/orphaned/unknown+rc/out 摘要/spill 指针。"""
        if self._async is None:
            return {"execution_id": execution_id, "status": "unknown"}
        return self._async.poll(execution_id)

    def pending_executions(self):
        """未回填异步执行全量 {id: 快照}（wait/巡检面）。"""
        return self._async.pending() if self._async else {}

    def _breaker_event(self, event):
        """断路器事件入账单源（主线程 report/allows 路径调用）。"""
        self._add_tl(event, self._ts())

    def _reap_async(self, iid, turn):
        """件a 收拢：已完成异步行→outcome 回填+事件入账+喂断路器。"""
        if self._async is None:
            return []
        out = []
        for r in self._async.take_ready():
            rc = r.get("rc")
            if rc is not None and self._breaker is not None:
                self._breaker.report(r["card"], rc, r.get("err", ""))
            self._add_tl(
                "warrior-progress warrior=%s intent=%s turn=%d "
                "op=async-result execution_id=%s card=%s rc=%s"
                % (self._warrior, iid, turn, r["execution_id"],
                   r["card"], rc), self._ts())
            out.append(
                "tool %s rc=%s out=%s err=%s (异步回填 execution_id=%s)"
                % (r["card"], rc, flat(r.get("out", "")),
                   flat(r.get("err", "")), r["execution_id"]))
        return out

    # ---- tool 并行批（律①③④+F22 三件）----

    def _run_tool_batch(self, batch, iid, turn, corr):
        # 调前自纠预检：主线程按派发序串行（corrections 层非线程安全）
        pre_by_idx = {}
        for idx, ins in batch:
            pre_by_idx[idx] = (
                corr.before_tool_call(ins["card"], ins["args"])
                if corr is not None else "")
        # 件b 断路器前置判定：主线程按派发序（熔断刀不进批——省火+零
        # 工作线程账本写，线程纪律不破）
        results = {}
        live = []
        for idx, ins in batch:
            if self._breaker is not None:
                ok, reason = self._breaker.allows(ins["card"])
                if not ok:
                    results[idx] = ((1, "", reason), 0, {"breaker": True})
                    continue
            live.append((idx, ins))
        # 分组：同卡同目标同组组内串行（律④）；组间并行（律①）
        groups = {}
        for idx, ins in live:
            groups.setdefault(dep_key(ins["card"], ins["args"]),
                              []).append((idx, ins))
        sem = threading.BoundedSemaphore(self.max_parallel)

        def group_run(entries):
            for idx, ins in entries:
                with sem:                       # 律①：信号量上限
                    self._exec_entry(idx, ins, iid, turn, results)

        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            for entries in groups.values():
                pool.submit(group_run, entries)
        # 律③：完成序解耦——主线程按派发序收拢入账（律②：串行入账原序）
        outcomes, signals = [], []
        for idx, ins in batch:
            (rc, out, err), dur, meta = results[idx]
            if "async" in meta:                  # 件a：发卡即回 execution_id
                eid = meta["async"]
                self._add_tl(
                    "warrior-progress warrior=%s intent=%s turn=%d "
                    "op=async-submit execution_id=%s card=%s call=%d"
                    % (self._warrior, iid, turn, eid, ins["card"], idx),
                    self._ts())
                outcomes.append(
                    "tool %s async execution_id=%s 已转后台"
                    "（超%.0fs未完不占轮次，结果后续轮次自动回填）"
                    % (ins["card"], eid, self._async_threshold_s))
                continue
            signal = None
            if corr is not None:
                raw = out if not err else "%s\n%s" % (out, err)
                signal = corr.after_tool_call(
                    ins["card"], ins["args"], raw,
                    duration_ms=dur, rc=rc,
                    error=(err.strip() or None) if rc != 0 else None)
            self._add_tl(
                "warrior-progress warrior=%s intent=%s turn=%d op=tool "
                "card=%s rc=%d call=%d"
                % (self._warrior, iid, turn, ins["card"], rc, idx),
                self._ts())
            try:                                 # 件c：超限落盘+摘要指针
                out_v, err_v, _sp = spill_output(
                    self._goal_dir, ins["card"], out, err,
                    self._spill_threshold)
            except Exception:                    # noqa: BLE001
                out_v, err_v = out, err
            summary = "tool %s rc=%d out=%s err=%s" % (
                ins["card"], rc, flat(out_v), flat(err_v))
            note = correction_note(pre_by_idx.get(idx, ""),
                                   signal.model_hint()
                                   if signal is not None else "")
            if note:
                summary += "\n" + note
            outcomes.append(summary)
            if not meta.get("breaker") and self._breaker is not None:
                self._breaker.report(ins["card"], rc, err)
            if signal is not None:
                signals.append(signal)
        return outcomes, signals

    def _exec_entry(self, idx, ins, iid, turn, results):
        """单刀执行：件a 有界等待（超时转后台发卡）；纯同步=零异步池老路。

        断路器判定在 _run_tool_batch 主线程前置完成（熔断刀不进批）。"""
        card = ins["card"]
        t0 = self._clock()
        thr = self._async_threshold_s if self._async is not None else 0.0
        if not thr or thr <= 0.0:
            # 零异步池装配（goal_dir 缺省）=纯同步老路
            try:
                r = self._tool_exec(card, ins["args"])
            except Exception as e:               # noqa: BLE001
                r = (2, "", "tool 通道异常: %s" % e)
            results[idx] = (r, int((self._clock() - t0) * 1000), {})
            return
        exec_id = mint_execution_id(iid, turn, idx)
        holder, done, handed = {}, threading.Event(), {"v": False}
        lk = threading.Lock()

        def _bg():
            try:
                r = self._tool_exec(card, ins["args"])
            except Exception as e:               # noqa: BLE001
                r = (2, "", "tool 通道异常: %s" % e)
            with lk:
                if handed["v"]:                  # 已发卡：后台收口入池
                    rc, out, err = r
                    try:
                        out_v, err_v, sp = spill_output(
                            self._goal_dir, card, out, err,
                            self._spill_threshold)
                    except Exception:            # noqa: BLE001
                        out_v, err_v, sp = out, err, None
                    self._async.complete(exec_id, rc, out_v, err_v, sp,
                                         self._ts())
                else:                            # 等待窗内完成：交同步路
                    holder["r"] = r
            done.set()

        threading.Thread(target=_bg, daemon=True).start()  # 后台续跑线程
        if done.wait(max(0.0, thr)):
            results[idx] = (holder["r"], int((self._clock() - t0) * 1000),
                            {})
            return
        with lk:
            if "r" in holder:                    # 完成与超时同瞬：同步收
                results[idx] = (holder["r"],
                                int((self._clock() - t0) * 1000), {})
                return
            self._async.register(exec_id, card, self._ts())
            handed["v"] = True
        results[idx] = ((None, "", ""), 0, {"async": exec_id})

    # ---- ledger 屏障（律②）----

    def _exec_ledger(self, ins, iid, turn):
        args = dict(ins["args"])
        args.pop("timestamp", None)
        if ins["cmd"] in ("add-fact", "add-finding"):
            args["intent-id"] = iid      # 只为本意图落账（防跨写）
        args["timestamp"] = self._ts()
        rc, out = self._ledger_write(ins["cmd"], args)
        self._add_tl(
            "warrior-progress warrior=%s intent=%s turn=%d op=ledger "
            "cmd=%s rc=%d" % (self._warrior, iid, turn, ins["cmd"], rc),
            self._ts())
        return "ledger %s rc=%d %s" % (ins["cmd"], rc, flat(out, 300))
