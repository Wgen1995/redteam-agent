# -*- coding: utf-8 -*-
"""同轮指令并行执行器（E 舰吸收件③：cyber-harness loop.go:498 语义对齐）。

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
"""
import threading
from concurrent.futures import ThreadPoolExecutor

from .corrections import correction_note

MAX_PARALLEL_TOOLS = 16        # 信号量上限（cyber-harness defaults.go:15 同源）
_UNPARSED_TARGET = "*"         # 目标不可辨：同卡全串行（保守）


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
    （tool_exec/ledger_write/now/add_tl）——loop 装配、单测假件直挂。"""

    def __init__(self, tool_exec, ledger_write, now, ts, add_tl, warrior_id,
                 max_parallel=MAX_PARALLEL_TOOLS):
        """端口注入：now=浮点钟（时延计量）、ts=ISO 时戳铸造（入账面），
        add_tl=timeline 事件单源写方，ledger_write=registry 写命令面。"""
        self._tool_exec = tool_exec
        self._ledger_write = ledger_write
        self._clock = now
        self._ts = ts
        self._add_tl = add_tl
        self._warrior = warrior_id
        self.max_parallel = max(1, int(max_parallel))

    # ---- 主入口 ----

    def execute(self, instructions, iid, turn, corr=None):
        """指令列表（派发序）→ BatchResult。done 即止（其后指令不执行，
        与既有串行语义一致）；每条非 done 恰产一条 outcome（派发序）。"""
        outcomes, signals = [], []
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

    # ---- tool 并行批（律①③④）----

    def _run_tool_batch(self, batch, iid, turn, corr):
        # 调前自纠预检：主线程按派发序串行（corrections 层非线程安全）
        pre_by_idx = {}
        for idx, ins in batch:
            pre_by_idx[idx] = (
                corr.before_tool_call(ins["card"], ins["args"])
                if corr is not None else "")
        # 分组：同卡同目标同组组内串行（律④）；组间并行（律①）
        groups = {}
        for idx, ins in batch:
            groups.setdefault(dep_key(ins["card"], ins["args"]),
                              []).append((idx, ins))
        results = {}
        sem = threading.BoundedSemaphore(self.max_parallel)

        def group_run(entries):
            for idx, ins in entries:
                with sem:                       # 律①：信号量上限
                    t0 = self._clock()
                    try:
                        rc, out, err = self._tool_exec(ins["card"],
                                                       ins["args"])
                    except Exception as e:       # noqa: BLE001
                        rc, out, err = 2, "", "tool 通道异常: %s" % e
                    dur = int((self._clock() - t0) * 1000)
                results[idx] = ((rc, out, err), dur)

        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            for entries in groups.values():
                pool.submit(group_run, entries)
        # 律③：完成序解耦——主线程按派发序收拢入账（律②：串行入账原序）
        outcomes, signals = [], []
        for idx, ins in batch:
            (rc, out, err), dur = results[idx]
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
            summary = "tool %s rc=%d out=%s err=%s" % (
                ins["card"], rc, flat(out), flat(err))
            note = correction_note(pre_by_idx.get(idx, ""),
                                   signal.model_hint()
                                   if signal is not None else "")
            if note:
                summary += "\n" + note
            outcomes.append(summary)
            if signal is not None:
                signals.append(signal)
        return outcomes, signals

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
