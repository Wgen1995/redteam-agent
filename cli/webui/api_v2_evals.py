# -*- coding: utf-8 -*-
"""api_v2_evals（T7·P8-P18 评测对比页）——D2 三臂同考只读投影，
路由 /api/v2/evals.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性）；挂载=ROUTES 单源表由 include 机制
（api_pages.py，UI-1 舰）分发——挂法钉在 tests/test_webui_pagespec_evals.py
（_V2MountHandler）：会话门复用 Handler._session_ok，缺会话=401 JSON。

数据单源（spec §P8-P18 评测对比=D2 三臂同考读面）：
  登记处   = experiments/<exp-id>.tsv——行式解析单源复用 webui.metrics.
             parse_exp_tsv（不造第二份格式）；列文件逐读保留全字段
             （experiments_view 只回 11 规范字段会丢 battles_<臂名>——本域
             需要全字段做通用臂解析）；逐字上屏律：question/status/verdict/
             note 原样透传不润色；
  臂解析   = battles_<name> 字段通用解析（双臂/三臂同律——登记字段即臂名），
             战例 token（b29 / battle-29 两式）→ battles_metrics 结算行联表；
  结算行   = webui.metrics.battles_metrics（settle-report recall 行单源）；
             未结算战例如实标「未结算」计数，不造数（诚实法条）；
  D2 判定  = id 以 d2 起头的登记=三臂同考；未登记=诚实空态+预登记律提示
             （开战前先落 tsv——无登记=本页不认）。
"""
import os
import re

from . import metrics as _metrics

ROUTE_EVALS = "/api/v2/evals.json"
ROUTES = {ROUTE_EVALS: None}                           # 尾部赋真身（前向引用）

_ARM_FIELD = re.compile(r"^battles_([A-Za-z0-9\-]+)$")
_BATTLE_TOKEN = re.compile(r"^(?:b(?:attle)?)[-_]?(\d+)$", re.I)

_PRE_REG_HINT = ("预登记律：开战前先落 experiments/<exp-id>.tsv（battles_<臂名> "
                 "字段列战例，registered=登记时间）——无登记=本页不认。")


def _battle_no(token):
    m = _BATTLE_TOKEN.match(token.strip())
    return int(m.group(1)) if m else None


def _arm_of(exp_doc, field, battles_by_no):
    """battles_<name> 字段 → 臂行 {name, battles[], settled, unsettled, mean_recall,
    min_recall, max_recall, hits, total}（未结算如实计数）。"""
    name = _ARM_FIELD.match(field).group(1)
    tokens = [t for t in str(exp_doc.get(field) or "").split() if t]
    settled = []
    unsettled = 0
    rows = []
    for t in tokens:
        no = _battle_no(t)
        row = battles_by_no.get(no) if no is not None else None
        if row is None:
            unsettled += 1
            rows.append({"battle": t, "recall": None})
        else:
            settled.append(row)
            rows.append({"battle": t, "recall": row["recall"]})
    recalls = [r["recall"] for r in settled]
    return {
        "name": name,
        "battles": tokens,
        "rows": rows,
        "settled": len(settled),
        "unsettled": unsettled,
        "mean_recall": round(sum(recalls) / len(recalls), 4) if recalls else None,
        "min_recall": min(recalls) if recalls else None,
        "max_recall": max(recalls) if recalls else None,
        "hits": sum(r["hits"] for r in settled),
        "total": sum(r["total"] for r in settled),
    }


def _registry_docs(repo_root=None):
    """登记处 → [raw dict]（parse_exp_tsv 单源解析；保留全字段；无 id 跳过）。"""
    exp_dir = os.path.join(repo_root or _metrics.default_repo_root(), "experiments")
    try:
        names = sorted(os.listdir(exp_dir))
    except OSError:
        return []
    out = []
    for name in names:
        if not name.endswith(".tsv"):
            continue
        try:
            with open(os.path.join(exp_dir, name), encoding="utf-8",
                      errors="replace") as f:
                doc = _metrics.parse_exp_tsv(f.read())
        except OSError:
            continue
        if doc.get("id"):
            out.append(doc)
    out.sort(key=lambda d: d["id"])
    return out


def evals_view(repo_root=None, battles_dir=None):
    """评测对比投影 → {experiments[], d2{registered,experiments,hint},
    counts, note}。只读零写入。"""
    docs = _registry_docs(repo_root)
    bm = _metrics.battles_metrics(battles_dir)
    battles_by_no = {b["n"]: b for b in bm["battles"]}

    experiments = []
    d2_exps = []
    for doc in docs:
        # 臂序=登记文件字段序（parse_exp_tsv 按行插入——登记序即展示序）
        arms = [_arm_of(doc, f, battles_by_no) for f in doc
                if _ARM_FIELD.match(f)]
        row = {
            "id": doc.get("id", ""), "question": doc.get("question", ""),
            "registered": doc.get("registered", ""),
            "status": doc.get("status", ""), "verdict": doc.get("verdict", ""),
            "decision_rule": doc.get("decision_rule", ""),
            "gt_gen": doc.get("gt_gen", ""), "source": doc.get("source", ""),
            "note": doc.get("note", ""),
            "arms": arms, "arm_count": len(arms),
        }
        experiments.append(row)
        if doc.get("id", "").startswith("d2"):
            d2_exps.append(row)

    return {
        "experiments": experiments,
        "d2": {
            "registered": bool(d2_exps),
            "experiments": d2_exps,
            "hint": "" if d2_exps else _PRE_REG_HINT,
        },
        "counts": {
            "experiments": len(experiments),
            "d2": len(d2_exps),
            "settled_battles": len(bm["battles"]),
        },
        "note": ("臂=battles_<臂名> 登记字段；均值=已结算战例 recall 的算术平均，"
                 "未结算战例单独计数不进均值——n 小判不了产品间显著性，跨臂只报"
                 "区间不判显著（登记 note 原样上屏）。"),
    }


def _evals_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = evals_view(battles_dir=battles_dir)
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "评测对比参数无效: %s" % e}
    return 200, payload


ROUTES[ROUTE_EVALS] = _evals_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
