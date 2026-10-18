# -*- coding: utf-8 -*-
"""api_v2_capability（演进飞轮②能力曲线）——每仗评测聚合只读投影，
路由 /api/v2/capability.json。设计权威 docs/design/evolution-flywheel-v1.md
「能力度量面」：召回率(vs GT)/误报率(verified-only 证伪面)/每美元发现数/
覆盖率——能力曲线随仗编号画线；曲线下降段=告警旗（不是等客户骂）。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性——同输入两跑逐字节一致）；挂载=ROUTES 单源表由
include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_capability.py（_V2MountHandler）：会话门复用
Handler._session_ok，缺会话=401 JSON。dispatch(path, query, ledger_dir,
battles_dir) 与 api_v2_techniques 同形（本域不依赖账本参数，入参原样收下）。

数据单源（metrics.py 同源勘定，跨舰零 import 自洽）:
  召回    = <battle>/settle-report.txt 的 recall=H/T 行（scripts/battle.py
            cmd_settle→tests/eval_range_recall.py 产物流）；未结算=不入曲线
            只入计数（诚实降级，不虚造点）。
  误报    = 活发现集内重放证伪（timeline replay:FD/EV REJECTED+replay-probe
            not-reproduced——G-52 事件溯源末值口径，gate.fp_of_session 同律）。
  每美元  = budget.tsv dollars_delta 合计；hits/美元；零美元=None（未计量
            不虚造）。
  覆盖率  = matrix.tsv 格阵终态 x 占比（同格后代行胜——api_v2_coverage
            事件溯源同构）；无矩阵=None。
  臂标    = directive.txt 字节数（>0 处置/=0 对照/缺=未知——metrics.py 同法）。
  知识位  = 仓 knowledge 存量（concepts 技法卡+negative 避坑卡——飞轮
            knowledge stock；避坑卡计数读 ng-index.tsv 行数）。

告警旗（曲线下降段）：相邻仗对（时间序=仗编号升序）逐段检——召回/覆盖/
每美元回落+误报率上升；None 值跳过（未计量段不判）；文案宪法#41 人话
（metric_zh 中文直读）。
"""
import os
import re

ROUTE_CAP = "/api/v2/capability.json"
ROUTES = {ROUTE_CAP: None}                          # 尾部赋真身（前向引用）

_BATTLE = re.compile(r"^battle-(\d+)$")
_RECALL = re.compile(r"recall=([0-9.]+) \((\d+)/(\d+)\)")
_MISSING = re.compile(r"^MISSING\t(\S+)", re.M)
_REPLAY = re.compile(r"^replay:(\S+?):(VERIFIED|REPAIRED|REJECTED)")
_PROBE = re.compile(r"replay-probe (\S+) verdict=(\S+)")

ARM_CONTROL, ARM_TREAT, ARM_UNKNOWN = "对照", "处置", "未知"


def _repo_root():
    """仓根=本文件（cli/webui/api_v2_capability.py）上三级。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def default_battles_dir():
    """默认 battle 根=TANYIN_HOME（或 ~/.tanyin）/battles——battle.py BASE 同源。"""
    home = os.environ.get("TANYIN_HOME") or os.path.join(
        os.path.expanduser("~"), ".tanyin")
    return os.path.join(home, "battles")


def default_knowledge_dir():
    return os.path.join(_repo_root(), "knowledge")


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_table(path):
    """账本表读 → 行集（冻结列序，无表头为主形——真实 battle 会话=schemas.py
    TABLES 列序裸行；夹具带表头形同吃：首列==列名即让行）。缺文件=空。"""
    text = _read_text(path)
    if text is None:
        return []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    rows = [ln.split("\t") for ln in lines]
    if rows and rows[0] and rows[0][0] in ("id", "timestamp", "attack_surface"):
        rows = rows[1:]
    return rows


# 账本冻结列位（schemas.py TABLES 单源；真实会话无表头——列序=契约锚）：
# findings 19 列 id=0/evidence_ids=13/control_evidence_ids=14/status=16
# （tests 侧 TABLES 断言钉——列位漂移=测试红）；timeline 8 列 event=3；
# budget 8 列 dollars_delta=4；matrix 8 列 attack_surface=0/vuln_class=1/
# state=2。
_FINDINGS_W, _TIMELINE_W, _BUDGET_W, _MATRIX_W = 19, 8, 8, 8
_FI_ID, _FI_EV, _FI_CEV, _FI_STATUS = 0, 13, 14, 16
_TI_EVENT, _BI_DOLLARS = 3, 4
_MI_SURF, _MI_VULN, _MI_STATE = 0, 1, 2


def _gen_of(home):
    """battle 目录内 G-* 会话目录：主代优先（(首数字,名) 字典序首位——
    "G-r30" 排在 "G-r30.bak-preReplay" 前，.bak/.corrupt 备份族不夺位）；
    缺=None。"""
    try:
        names = [n for n in os.listdir(home)
                 if n.startswith("G-") and os.path.isdir(os.path.join(home, n))]
    except OSError:
        return None

    def key(name):
        ds = [int(d) for d in re.findall(r"\d+", name)]
        return ((ds or [0])[0], name)
    return sorted(names, key=key)[0] if names else None


def _battle_arm(home):
    try:
        return ARM_TREAT if os.path.getsize(
            os.path.join(home, "directive.txt")) > 0 else ARM_CONTROL
    except OSError:
        return ARM_UNKNOWN


def _fp_of(session):
    """误报面（gate.fp_of_session 同律）：活发现集内重放证伪 → (fp, active)。"""
    frows = _read_table(os.path.join(session, "findings.tsv"))
    latest = {}
    for r in frows:
        if len(r) == _FINDINGS_W:
            latest[r[_FI_ID]] = r
    if not latest:
        return 0, 0
    active = [r for r in latest.values() if r[_FI_STATUS] in ("", "active")]
    state, probe_last = {}, {}
    for r in _read_table(os.path.join(session, "timeline.tsv")):
        if len(r) != _TIMELINE_W:
            continue
        ev = r[_TI_EVENT]
        m = _REPLAY.match(ev)
        if m:
            state[m.group(1)] = m.group(2)
        m2 = _PROBE.search(ev)
        if m2:
            probe_last[m2.group(1)] = m2.group(2)
    blocked = {i for i, v in probe_last.items() if v == "not-reproduced"}
    blocked |= {i for i, v in state.items()
                if i.startswith("EV-") and v == "REJECTED"}
    fp = 0
    for r in active:
        evs = [x for x in r[_FI_EV].split(";") if x]
        evs += [x for x in r[_FI_CEV].split(";") if x]
        if state.get(r[_FI_ID]) == "REJECTED" or any(e in blocked for e in evs):
            fp += 1
    return fp, len(active)


def _dollars_of(session):
    total = 0.0
    for r in _read_table(os.path.join(session, "budget.tsv")):
        if len(r) == _BUDGET_W:
            try:
                total += float(r[_BI_DOLLARS]) if str(r[_BI_DOLLARS]).strip() else 0.0
            except ValueError:
                continue
    return round(total, 4)


def _coverage_of(session):
    """matrix 格阵终态 x 占比（同格后代行胜）；无矩阵=None（未测面）。"""
    latest = {}
    for r in _read_table(os.path.join(session, "matrix.tsv")):
        if len(r) == _MATRIX_W:
            latest[(r[_MI_SURF], r[_MI_VULN])] = r[_MI_STATE]
    if not latest:
        return None
    x = sum(1 for v in latest.values() if v == "x")
    return round(x / len(latest), 4)


def knowledge_stock(knowledge_dir=None):
    """knowledge 存量：concepts 技法卡数+negative 避坑卡数（ng-index 行数）。"""
    kd = knowledge_dir if knowledge_dir is not None else default_knowledge_dir()
    try:
        n_cp = sum(1 for n in os.listdir(os.path.join(kd, "concepts"))
                   if re.match(r"^CP-\d+\.md$", n))
    except OSError:
        n_cp = 0
    ng_rows = _read_table(os.path.join(kd, "negative", "ng-index.tsv"))
    n_ng = sum(1 for r in ng_rows if len(r) >= 1 and r[0].startswith("CP-"))
    return {"technique_cards": n_cp, "negative_cards": n_ng}


_METRIC_ZH = {"recall": "召回率", "fp_rate": "误报率", "coverage": "覆盖率",
              "per_dollar": "每美元发现"}


def _decline_warnings(series):
    """曲线下降段=告警旗：相邻仗对逐段检（None 值跳过——未计量段不判）。
    高优指标（召回/覆盖/每美元）回落+误报率上升；旗带 from/to 仗号与值。"""
    out = []
    for i in range(1, len(series)):
        a, b = series[i - 1], series[i]
        for metric, kind in (("recall", "回落"), ("coverage", "回落"),
                             ("per_dollar", "回落"), ("fp_rate", "上升")):
            va, vb = a.get(metric), b.get(metric)
            if va is None or vb is None:
                continue
            bad = vb > va if metric == "fp_rate" else vb < va
            if bad:
                out.append({"metric": metric, "metric_zh": _METRIC_ZH[metric],
                            "type": kind, "from_n": a["n"], "to_n": b["n"],
                            "from_v": va, "to_v": vb,
                            "note": "%s%s：仗%d %.4f → 仗%d %.4f"
                                    % (_METRIC_ZH[metric], kind,
                                       a["n"], va, b["n"], vb)})
    return out


def capability_view(battles_dir=None, knowledge_dir=None):
    """能力曲线投影（只读零写入）：series=已结算仗时间序+warnings 下降段旗+
    counts+knowledge 存量。未结算/坏目录降级不炸（counts 披露）。"""
    bdir = battles_dir if battles_dir is not None else default_battles_dir()
    try:
        names = sorted(os.listdir(bdir))
    except OSError:
        names = []
    series, seen = [], 0
    for name in names:
        m = _BATTLE.match(name)
        if not m:
            continue
        seen += 1
        home = os.path.join(bdir, name)
        report = _read_text(os.path.join(home, "settle-report.txt"))
        if report is None:
            continue
        rm = _RECALL.search(report)
        if not rm:
            continue                          # 未结算（无召回行）=不入曲线
        hits, total = int(rm.group(2)), int(rm.group(3))
        gen = _gen_of(home)
        session = os.path.join(home, gen) if gen else home
        fp, active = _fp_of(session)
        dollars = _dollars_of(session)
        series.append({
            "n": int(m.group(1)), "id": name, "arm": _battle_arm(home),
            "recall": round(hits / total, 4) if total else 0.0,
            "hits": hits, "total": total,
            "missing_n": len(_MISSING.findall(report)),
            "fp": fp, "active": active,
            "fp_rate": round(fp / active, 4) if active else 0.0,
            "findings": active,
            "dollars": dollars,
            "per_dollar": round(hits / dollars, 4) if dollars > 0 else None,
            "coverage": _coverage_of(session),
        })
    series.sort(key=lambda b: b["n"])
    warnings = _decline_warnings(series)
    return {
        "series": series,
        "warnings": warnings,
        "flagged_battles": sorted({b for w in warnings
                                    for b in (w["from_n"], w["to_n"])}),
        "counts": {"battles_seen": seen, "battles_settled": len(series),
                   "warnings": len(warnings)},
        "knowledge": knowledge_stock(knowledge_dir),
    }


def _capability_route(query, ledger_dir=None, battles_dir=None):
    return 200, capability_view(battles_dir=battles_dir)


ROUTES[ROUTE_CAP] = _capability_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
