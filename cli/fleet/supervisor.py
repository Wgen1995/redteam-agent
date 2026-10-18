# -*- coding: utf-8 -*-
"""多任务治理舰（功能25补件）·件①：多仗常驻总控 supervisor。

来源：docs/design/2026-10-20-build-master-plan.md R14（多任务治理舰：总并发帽+
supervisor 舰队化——审计证实原为纯设计）+裁决书 §十八（全局资源治理缺件）。

与 planner_loop 的分界（本模块 docstring 即声明，tests/test_fleet_supervisor.py
TestPlannerBoundary 钉死）：planner_loop=单仗内规划者（一仗 goal 内可达空格×
五因子→add-intent 派活）；本模块=仗间总控（多仗并发帽/排队/仗级优先级/停续查
/全停阀/断电恢复）。本模块零意图铸造（不 import planner、不碰 add-intent）、
零单仗进程管理（点火/杀树=既有 battle 控制面，不在本舰）。

Ruling（tests/test_fleet_supervisor.py 同源钉）：
- R-FLT-1 全局并发帽：cap_soldiers=全舰队总士兵上限（fleet.json 可配）；
  Σactive.soldiers+新仗申报≤帽→active；超帽→queued（排队不开工，绝不缩配
  抢跑——余量装不下整队就让位）。headroom=帽-Σactive。
- R-FLT-2 单仗配额继承：register 不报 soldiers=继承 per_battle_soldiers；
  显式申报须≥1；预算申报须非负有限（battle_registry 数学纪律同律）。
- R-FLT-3 仗级优先级五因子（复用 planner_score 五因子思想、输入换仗级）：
  budget_margin 预算余量/deadline_urgency 截止紧迫/heat 白热（近窗账本活跃）/
  yield 发现产出/wait_age 排队等待——各 0-1 加权和（权重和≤1 fail-loud）、
  factor_detail 全因子入串（可解释律）、同分按仗名自然序（确定性）。
  帽满时谁先开工=此排序（排队律的仲裁面）。
- R-FLT-4 停/续/查三命令面：stop(battle)→paused+对该仗账本可见的全部战士
  铸 warrior-stop（复用 warrior.steer 既有 halt 单源——战士 scan 即停，本模块
  不私造停信号格式）+fleet-stop 留痕行；resume(battle)→active（帽满→queued
  诚实排队）；resume(None)=舰队级续（清全停+促升格）；status()=帽余量/队列/
  停摆一览。全部幂等：二停零追加、终态仗停=无事。
- R-FLT-5 全停阀：emergency_stop=halted 旗入 fleet-meta.tsv（跨重启持久）+
  所有非终态仗 paused+每仗 timeline 铸 warrior-stop（账本可见的全部战士 id）
  +fleet-halt 留痕——停后 promote/register 全不开工（无新意图铸出：队列冻结、
  新仗只排队）；halted 恢复不复活（recover 零变更）。
- R-FLT-6 心跳超时：tick() 从仗 timeline 同步 warrior-heartbeat（账本既有
  事实，不另造心跳协议）→fleet 心跳列；active 且心跳龄>timeout→failed
  （审计带因），腾帽促升格。
- R-FLT-7 断电恢复：recover()=读注册表重建在途集（active 原样保留不双开、
  queued 原样排队、终态不动、halted 持久）——恢复零审计噪音（册即真相）。

写通道纪律：舰队册=fleet_state（TSV 单源+审计）；仗 timeline=append_tl_locked
（goal 锁内单源写方）+steer.write_stop（停信号格式单源）。零私铸 TSV。
"""
import json
import math
import os
import re
import time

from ledger import timeline as TL
from ledger.enforce import parse_ts
from warrior import heartbeat as _hb
from warrior import steer

from . import fleet_state as fs

CONFIG_NAME = "fleet.json"

DEFAULT_WEIGHTS = {
    "budget_margin": 0.30,        # 预算余量（余量足者值得占槽）
    "deadline_urgency": 0.25,     # 截止紧迫（临期者先）
    "heat": 0.20,                 # 白热程度（近窗活跃者保温）
    "yield": 0.10,                # 发现产出（出过货的仗优先续力）
    "wait_age": 0.15,             # 排队等待（防饿死公平项）
}
DEFAULT_CONFIG = {
    "cap_soldiers": 10,           # 全局并发帽：总士兵数上限
    "per_battle_soldiers": 3,     # 单仗配额缺省（register 未申报即继承）
    "heartbeat_timeout_s": 900.0, # 心跳超时窗（active 判僵死）
    "heat_window_s": 900.0,       # 白热统计窗（近 15min 账本活跃）
    "heat_full_events": 20.0,     # 窗内满热事件数
    "yield_full": 5.0,            # 满产出发现数
    "wait_full_s": 3600.0,        # 满等待龄（1h 排队=满公平分）
    "deadline_urgent_s": 86400.0, # ≤24h 到期=最紧迫
    "deadline_far_s": 604800.0,   # ≥7d 到期=不紧迫
    "weights": dict(DEFAULT_WEIGHTS),
}

_FACTOR_ORDER = ("budget_margin", "deadline_urgency", "heat", "yield",
                 "wait_age")
_POSITIVE_FLOAT_KEYS = ("heartbeat_timeout_s", "heat_window_s",
                        "heat_full_events", "yield_full", "wait_full_s",
                        "deadline_urgent_s", "deadline_far_s")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_WARRIOR_EV_RE = re.compile(r"^warrior-(?:start|heartbeat)\s+.*?warrior=(\S+)")
_HB_RE = re.compile(r"^warrior-heartbeat\s")


# ---------------------------------------------------------------- 配置（fail-loud）

def _validate(cfg):
    """配置校验 fail-loud（planner_score.load_config 同律：错配置拒启）。"""
    for key in ("cap_soldiers", "per_battle_soldiers"):
        v = cfg[key]
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise ValueError("%s 须正整数: %r" % (key, v))
    for key in _POSITIVE_FLOAT_KEYS:
        v = float(cfg[key])
        if not (v > 0 and math.isfinite(v)):
            raise ValueError("%s 须正有限数: %r" % (key, cfg[key]))
        cfg[key] = v
    w = cfg["weights"]
    if not isinstance(w, dict):
        raise ValueError("weights 须对象")
    for k, v in w.items():
        if k not in DEFAULT_WEIGHTS:
            raise ValueError("未知权重因子 %s（合法集=%s）"
                             % (k, sorted(DEFAULT_WEIGHTS)))
        try:
            fv = float(v)
        except (TypeError, ValueError):
            raise ValueError("权重 %s 非数值: %r" % (k, v))
        if fv < 0:
            raise ValueError("权重 %s 为负: %r" % (k, v))
        w[k] = fv
    total = sum(w.values())
    if total > 1.0 + 1e-9:
        raise ValueError("权重和 %.6f>1" % total)
    return cfg


def load_config(root):
    """fleet.json → 合并缺省后的全量配置；缺文件=全缺省；坏配置=ValueError。"""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))   # 深拷贝缺省
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.isfile(path):
        return _validate(cfg)
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except ValueError as e:
        raise ValueError("fleet.json 非法 JSON: %s" % e)
    if not isinstance(raw, dict):
        raise ValueError("fleet.json 须为 JSON 对象")
    for key in ("cap_soldiers", "per_battle_soldiers"):
        if key in raw:
            cfg[key] = raw[key]
    for key in _POSITIVE_FLOAT_KEYS:
        if key in raw:
            cfg[key] = raw[key]
    if "weights" in raw:
        cfg["weights"].update(raw["weights"] or {})
    return _validate(cfg)


# ---------------------------------------------------------------- 仗级五因子（纯函数）

def _clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _to_f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def battle_factors(stats, now_epoch, config):
    """仗级五因子+加权和（纯函数：stats×now×config→(score, factors)）。

    stats={budget_used_usd, budget_cap_usd, deadline, recent_events,
    findings, queued_at}——全仗级输入（预算余量/截止/白热=设计三主输入，
    产出/等待=防饿死与续力补充，五因子形承 planner_score）。
    未知帽=中性 0.5（诚实：不装懂）；无截止=中性 0.5。
    """
    cap = _to_f(stats.get("budget_cap_usd"))
    if cap > 0:
        budget_margin = _clamp01(1.0 - _to_f(stats.get("budget_used_usd")) / cap)
    else:
        budget_margin = 0.5
    deadline_urgency = 0.5
    dl = stats.get("deadline")
    if dl:
        try:
            remaining = parse_ts(dl) - now_epoch
        except (ValueError, TypeError):
            remaining = None
        if remaining is not None:
            urgent, far = config["deadline_urgent_s"], config["deadline_far_s"]
            if remaining <= urgent:
                deadline_urgency = 1.0
            elif remaining >= far:
                deadline_urgency = 0.0
            else:
                deadline_urgency = 1.0 - (remaining - urgent) / (far - urgent)
    heat = _clamp01(_to_f(stats.get("recent_events"))
                    / float(config["heat_full_events"]))
    yld = _clamp01(_to_f(stats.get("findings")) / float(config["yield_full"]))
    wait_age = 0.0
    qa = stats.get("queued_at")
    if qa:
        try:
            waited = now_epoch - parse_ts(qa)
        except (ValueError, TypeError):
            waited = 0.0
        wait_age = _clamp01(waited / float(config["wait_full_s"]))
    factors = {"budget_margin": budget_margin,
               "deadline_urgency": deadline_urgency,
               "heat": heat, "yield": yld, "wait_age": wait_age}
    score = sum(config["weights"].get(k, 0.0) * v
                for k, v in factors.items())
    return score, factors


def factor_detail(factors):
    """可解释律：全因子入串（planner_score._factor_detail 同形）。"""
    return "fleet 五因子 " + " ".join(
        "%s=%.4f" % (k, factors[k]) for k in _FACTOR_ORDER)


def rank_battles(rows, stats_by_battle, now_epoch, config):
    """仗行×五因子→降序排行（同分按仗名自然序——确定性）。

    行 priority 列回填 "%.4f"（排序快照）；返回 [{battle, score, priority,
    factors, row}]。stats 缺该仗=空态势（全中性因子）。
    """
    out = []
    for row in rows:
        stats = stats_by_battle.get(row["battle"]) or {}
        score, factors = battle_factors(stats, now_epoch, config)
        out.append({"battle": row["battle"], "score": score,
                    "priority": "%.4f" % score, "factors": factors,
                    "row": row})
    out.sort(key=lambda r: (-r["score"], fs.battle_key(r["battle"])))
    return out


def _flat(s):
    """白空间折叠单行（steer._flat 同律——账本行禁换行）。"""
    return " ".join(str(s).split())


# ---------------------------------------------------------------- 总控

class FleetSupervisor(object):
    """多仗常驻总控：并发帽/配额/优先级/停续查/全停/心跳/恢复。

    用法（生产）：FleetSupervisor(fleet_root).run()
    用法（测试）：now_fn/sleep 注入，tick() 单步驱动（PlannerLoop 同法）。
    """

    def __init__(self, root, *, config=None, now_fn=None, sleep=None):
        self.root = root
        if config is not None:
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            for k in ("cap_soldiers", "per_battle_soldiers"):
                if k in config:
                    merged[k] = config[k]
            for k in _POSITIVE_FLOAT_KEYS:
                if k in config:
                    merged[k] = config[k]
            if config.get("weights"):
                merged["weights"].update(config["weights"])
            self.config = _validate(merged)
        else:
            self.config = load_config(root)
        self.now = now_fn if now_fn is not None else time.time
        self.sleep = sleep if sleep is not None else time.sleep

    # ---- 钟与读面 ----

    def _iso(self, t):
        return _hb.iso_of(t)

    def _rows(self):
        return fs.rows(self.root)

    def _halted(self):
        return fs.meta(self.root).get("halted") == "1"

    def _active_soldiers(self, rows_=None):
        rows_ = self._rows() if rows_ is None else rows_
        total = 0
        for r in rows_:
            if r["state"] == "active":
                try:
                    total += int(str(r["soldiers"]).strip() or 0)
                except ValueError:
                    continue
        return total

    def _headroom(self, rows_=None):
        return int(self.config["cap_soldiers"]) - self._active_soldiers(rows_)

    # ---- 注册与并发帽（R-FLT-1/2）----

    def register(self, battle, goal_dir, *, soldiers=None, budget_usd=0.0,
                 budget_cap_usd=None, deadline=""):
        """注册新仗+并发帽仲裁：装得下→active；超帽/全停→queued（不开工）。"""
        if deadline and not _ISO_Z_RE.match(str(deadline)):
            raise ValueError("deadline 须 ISO Z 形（YYYY-MM-DDTHH:MM:SSZ）: %r"
                             % (deadline,))
        n = int(self.config["per_battle_soldiers"]) if soldiers is None \
            else int(soldiers)
        if n < 1:
            raise ValueError("soldiers 须≥1（零士兵仗不开工）: %r" % (soldiers,))
        budget_usd = float(budget_usd)
        if not math.isfinite(budget_usd) or budget_usd < 0:
            raise ValueError("budget_usd 须非负有限数: %r" % (budget_usd,))
        cap_usd = "" if budget_cap_usd is None else float(budget_cap_usd)
        iso = self._iso(self.now())
        v = fs.register(self.root, battle, goal_dir, soldiers=n,
                        budget_usd=budget_usd, budget_cap_usd=cap_usd,
                        deadline=deadline, now_iso=iso)
        if not v["registered"]:
            row = v["row"]
            return {"battle": battle, "registered": False,
                    "state": row["state"], "soldiers": row["soldiers"],
                    "reason": "already-registered"}
        if self._halted():
            return {"battle": battle, "registered": True, "state": "queued",
                    "soldiers": n, "reason": "fleet-halted（全停期只排队）"}
        headroom = self._headroom()
        if n <= headroom:
            fs.transition(self.root, battle, "active", now_iso=iso,
                          reason="admit headroom=%d need=%d" % (headroom, n))
            return {"battle": battle, "registered": True, "state": "active",
                    "soldiers": n, "reason": ""}
        return {"battle": battle, "registered": True, "state": "queued",
                "soldiers": n,
                "reason": "cap-full headroom=%d need=%d cap=%d"
                          % (headroom, n, int(self.config["cap_soldiers"]))}

    # ---- 停/续/查三命令面（R-FLT-4）----

    def stop(self, battle, reason="操作员停仗"):
        """停仗：paused+warrior-stop 信号（既有 halt 单源）+留痕。幂等。"""
        row = fs.row_of(self.root, battle)
        if row is None:
            raise ValueError("未注册的仗: %r" % (battle,))
        if row["state"] in ("done", "failed"):
            return {"battle": battle, "changed": False, "state": row["state"],
                    "reason": "terminal（终态仗无事可停）"}
        if row["state"] == "paused":
            return {"battle": battle, "changed": False, "state": "paused",
                    "reason": "already-paused（幂等二停零追加）"}
        fs.transition(self.root, battle, "paused",
                      now_iso=self._iso(self.now()), reason=reason)
        self._signal(row, reason, verb="fleet-stop")
        return {"battle": battle, "changed": True, "state": "paused"}

    def resume(self, battle=None):
        """续仗：单仗=帽内 active/帽满 queued；无参=舰队级续（清全停+全暂停
        仗重入队+按优先级促升格——一切开工都走帽仲裁单径）。"""
        if battle is None:
            iso = self._iso(self.now())
            m = fs.set_meta(self.root, "halted", "0", now_iso=iso,
                            reason="fleet-resume")
            requeued = []
            for r in self._rows():
                if r["state"] == "paused":
                    fs.transition(self.root, r["battle"], "queued",
                                  now_iso=iso, reason="fleet-resume")
                    requeued.append(r["battle"])
            res = self.tick()
            return {"resumed_fleet": True, "cleared_halt": m["changed"],
                    "requeued": requeued, "promoted": res["promoted"]}
        row = fs.row_of(self.root, battle)
        if row is None:
            raise ValueError("未注册的仗: %r" % (battle,))
        if row["state"] in ("done", "failed"):
            return {"battle": battle, "changed": False, "state": row["state"],
                    "reason": "terminal"}
        if row["state"] == "active":
            return {"battle": battle, "changed": False, "state": "active",
                    "reason": "already-active"}
        try:
            need = int(str(row["soldiers"]).strip() or 0)
        except ValueError:
            need = 0
        iso = self._iso(self.now())
        if not self._halted() and 1 <= need <= self._headroom():
            fs.transition(self.root, battle, "active", now_iso=iso,
                          reason="resume headroom=%d" % self._headroom())
            return {"battle": battle, "changed": True, "state": "active",
                    "soldiers": need, "reason": ""}
        fs.transition(self.root, battle, "queued", now_iso=iso,
                      reason="resume-but-cap-full")
        return {"battle": battle, "changed": True, "state": "queued",
                "soldiers": need,
                "reason": "cap-full headroom=%d need=%d"
                          % (self._headroom(), need)}

    def status(self):
        """查仗：帽余量/队列/停摆/在途一览（零写入只读面）。"""
        rows_ = self._rows()
        by_state = dict((s, 0) for s in fs.STATES)
        for r in rows_:
            by_state[r["state"]] = by_state.get(r["state"], 0) + 1
        active_soldiers = self._active_soldiers(rows_)
        return {"halted": self._halted(),
                "cap_soldiers": int(self.config["cap_soldiers"]),
                "per_battle_soldiers": int(self.config["per_battle_soldiers"]),
                "active_soldiers": active_soldiers,
                "headroom": int(self.config["cap_soldiers"]) - active_soldiers,
                "queued": by_state.get("queued", 0),
                "battles": rows_}

    def finish(self, battle, reason="converged"):
        """收仗：→done（终态入册留史）。"""
        fs.transition(self.root, battle, "done",
                      now_iso=self._iso(self.now()), reason=reason)
        return {"battle": battle, "state": "done"}

    def fail(self, battle, reason="failed"):
        """败仗：→failed（审计带因）。"""
        fs.transition(self.root, battle, "failed",
                      now_iso=self._iso(self.now()), reason=reason)
        return {"battle": battle, "state": "failed"}

    # ---- 全停阀（R-FLT-5）----

    def emergency_stop(self, reason="emergency"):
        """全停：halted 旗+所有非终态仗 paused+每仗 warrior-stop 传播。幂等。"""
        iso = self._iso(self.now())
        was_halted = self._halted()
        rows_ = self._rows()
        to_pause = [r for r in rows_ if r["state"] not in
                    ("done", "failed", "paused")]
        signalled = []
        if not was_halted:
            fs.set_meta(self.root, "halted", "1", now_iso=iso, reason=reason)
        for r in to_pause:
            fs.transition(self.root, r["battle"], "paused", now_iso=iso,
                          reason="fleet-halt")
            self._signal(r, reason, verb="fleet-halt")
            signalled.append(r["battle"])
        return {"halted": True, "paused": signalled,
                "changed": bool(signalled) or not was_halted,
                "signalled": signalled}

    # ---- 心跳/升格/常驻（R-FLT-6）----

    def tick(self):
        """一轮总控：心跳同步→超时执法→（未全停）按优先级升格排队仗。"""
        now = float(self.now())
        iso = self._iso(now)
        synced, failed_stale = [], []
        for r in self._rows():
            if r["state"] != "active":
                continue
            hb = self._latest_heartbeat(r["goal_dir"])
            if hb and hb != r["heartbeat_at"]:
                fs.heartbeat(self.root, r["battle"], now_iso=hb)
                synced.append(r["battle"])
        for battle in fs.stale_battles(self.root, now,
                                       float(self.config[
                                           "heartbeat_timeout_s"])):
            fs.transition(self.root, battle, "failed", now_iso=iso,
                          reason="heartbeat-timeout")
            failed_stale.append(battle)
        promoted = []
        if not self._halted():
            for cand in self._ranked_queued(now):
                try:
                    need = int(str(cand["row"]["soldiers"]).strip() or 0)
                except ValueError:
                    continue
                if 1 <= need <= self._headroom():
                    fs.transition(self.root, cand["battle"], "active",
                                  now_iso=iso,
                                  reason="promote score=%s" % cand["priority"])
                    promoted.append(cand["battle"])
        return {"synced": synced, "failed_stale": failed_stale,
                "promoted": promoted}

    def run(self, max_rounds=None, interval=5.0):
        """常驻主循环（max_rounds=None=常驻；测试可限轮防死循环）。"""
        rounds = 0
        while max_rounds is None or rounds < max_rounds:
            self.tick()
            rounds += 1
            self.sleep(float(interval))
        return rounds

    # ---- 断电恢复（R-FLT-7）----

    def recover(self):
        """读注册表重建在途集：零变更零审计（册即真相——不双开不复活）。"""
        rows_ = self._rows()
        return {"in_flight": [r["battle"] for r in rows_
                              if r["state"] == "active"],
                "queued": [r["battle"] for r in rows_
                           if r["state"] == "queued"],
                "terminal": [r["battle"] for r in rows_
                             if r["state"] in ("done", "failed")],
                "halted": self._halted()}

    # ---- 内部：信号/态势 ----

    def _signal(self, row, reason, verb):
        """对该仗铸 warrior-stop（steer 单源）+舰队留痕行（append_tl_locked）。"""
        gd = row.get("goal_dir") or ""
        if not gd or not os.path.isdir(gd):
            return []
        ts = self._iso(self.now())
        stopped = []
        for wid in self._warriors(gd):
            steer.write_stop(gd, wid, "fleet: " + _flat(reason), ts)
            stopped.append(wid)
        TL.append_tl_locked(
            gd, ts, "%s battle=%s reason=%s" % (verb, row["battle"],
                                                _flat(reason)),
            actor=steer.ACTOR, phase="P-lifecycle")
        return stopped

    def _warriors(self, gd):
        """仗账本可见的全部战士 id（warrior-start/warrior-heartbeat 事件源）。"""
        out = set()
        try:
            rows_ = TL.read_rows(gd)
        except Exception:                          # noqa: BLE001 账本未生=无战士
            return []
        for r in rows_:
            if len(r) < 4:
                continue
            m = _WARRIOR_EV_RE.match(r[3])
            if m:
                out.add(m.group(1))
        return sorted(out)

    def _latest_heartbeat(self, gd):
        """该仗最近一条 warrior-heartbeat 的 ts（无=None）。"""
        if not gd or not os.path.isdir(gd):
            return None
        try:
            rows_ = TL.read_rows(gd)
        except Exception:                          # noqa: BLE001
            return None
        latest = None
        for r in rows_:
            if len(r) >= 4 and _HB_RE.match(r[3]):
                latest = r[0]
        return latest

    def _stats_for(self, row, now):
        """仗级五因子底表：册行字段+账本实况（白热=近窗行数/产出=发现数）。"""
        gd = row.get("goal_dir") or ""
        recent = 0
        findings = 0
        if gd and os.path.isdir(gd):
            try:
                tl_rows = TL.read_rows(gd)
                cutoff = now - float(self.config["heat_window_s"])
                for r in tl_rows:
                    if len(r) < 4:
                        continue
                    try:
                        if parse_ts(r[0]) >= cutoff:
                            recent += 1
                    except (ValueError, TypeError):
                        continue
                findings = self._count_tsv(gd, "findings.tsv")
            except Exception:                      # noqa: BLE001 态势读失败=空态势
                pass
        return {"budget_used_usd": row.get("budget_usd") or 0,
                "budget_cap_usd": row.get("budget_cap_usd") or 0,
                "deadline": row.get("deadline") or None,
                "recent_events": recent, "findings": findings,
                "queued_at": row.get("queued_at") or None}

    def _count_tsv(self, gd, name):
        path = os.path.join(gd, name)
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return sum(1 for ln in f if ln.strip())
        except OSError:
            return 0

    def _ranked_queued(self, now):
        """排队仗×五因子排行（priority 列回填=排序快照，无审计）。"""
        queued = [r for r in self._rows() if r["state"] == "queued"]
        stats = {r["battle"]: self._stats_for(r, now) for r in queued}
        ranked = rank_battles(queued, stats, now, self.config)
        iso = self._iso(now)
        for cand in ranked:
            fs.set_priority(self.root, cand["battle"], cand["priority"],
                            now_iso=iso)
        return ranked
