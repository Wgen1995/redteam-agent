# -*- coding: utf-8 -*-
"""webui metrics（v0.9c）——双臂战例度量装配（只读投影，零写入）。

数据真相（scripts/battle.py cmd_settle → tests/eval_range_recall.py 实勘）：
  <home>/battles/battle-N/settle-report.txt —— 首行 verify-chain（半/全角冒号两代
  容错），正文 recall=H/T 行 + MISSING\t<gt-id> 行；臂标记=directive.txt 字节数
  （>0=处置臂预置指令 / =0=对照臂 / 缺文件=早期战未知臂——多代格式降级）；
  GT 位=<home>/gt/<gen>.json（battle 目录 G-* 子目录即 gen，battle.py gt_out_path
  同源），缺 GT → per_item={}（McNemar 配对降级，图表照出不炸）。

McNemar exact（math.comb 双尾二项）与 scripts/rerun.py mcnemar_exact 逐点同口径
（已知活体样本 b=8 c=17 → p=0.107758≈0.108，N=5 双臂判决）。
"""
import json, os, re
from math import comb

ARM_CONTROL, ARM_TREAT = "对照", "处置"

_RECALL = re.compile(r"recall=([0-9.]+) \((\d+)/(\d+)\)")          # rerun._RECALL 同款
_MISSING = re.compile(r"^MISSING\t(\S+)", re.M)
_BATTLE = re.compile(r"^battle-(\d+)$")
_CHAIN = re.compile(r"verify-chain[:：]\s*(PASS|FAIL)")


def default_battles_dir():
    """默认路径=TANYIN_HOME（或 ~/.tanyin）/battles——battle.py BASE 同源。"""
    home = os.environ.get("TANYIN_HOME") or os.path.join(os.path.expanduser("~"), ".tanyin")
    return os.path.join(home, "battles")


def parse_settle(text):
    """settle 报告 → {recall,hits,total,missing,chain}；无 recall 行（未结算）→ None。"""
    m = _RECALL.search(text)
    if not m:
        return None
    hits, total = int(m.group(2)), int(m.group(3))
    cm = _CHAIN.search(text)
    return {"recall": round(hits / total, 4) if total else 0.0,
            "hits": hits, "total": total,
            "missing": _MISSING.findall(text),
            "chain": cm.group(1) if cm else ""}


def battle_arm(home):
    """臂标记：directive.txt >0B=处置（预置指令）/=0B=对照/缺文件=未知（早期战）。"""
    try:
        return ARM_TREAT if os.path.getsize(os.path.join(home, "directive.txt")) > 0 \
            else ARM_CONTROL
    except OSError:
        return None


def _gen_of(home):
    """battle 目录内 G-* 子目录即 gen（battle.py paths['goal'] 命名法）。"""
    try:
        for name in sorted(os.listdir(home)):
            if name.startswith("G-") and os.path.isdir(os.path.join(home, name)):
                return name
    except OSError:
        pass
    return None


def per_item_map(home, battles_dir, missing):
    """GT 项结局图 {gt_id: hit}：GT=<home>/gt/<gen>.json（battle 目录树外兄弟位）；
    缺 GT/坏 JSON → {}（降级：配对无分母，明细表 missing 清单仍可用）。"""
    gen = _gen_of(home)
    if gen is None:
        return {}
    gp = os.path.join(os.path.dirname(os.path.abspath(battles_dir)), "gt", gen + ".json")
    try:
        with open(gp, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return {}
    entries = (doc.get("planted") or doc.get("entries") or doc.get("items") or []
               if isinstance(doc, dict) else doc)
    out = {}
    for e in entries:
        eid = e.get("id") if isinstance(e, dict) else None
        if eid:
            out[str(eid)] = str(eid) not in missing
    return out


def mcnemar_exact(items_a, items_b):
    """两臂逐 GT 配对精确 McNemar（双尾二项；口径=scripts/rerun.py mcnemar_exact）。

    只对两臂共有 GT 项集合配对：b=A 命中而 B 未命中，c=A 未命中而 B 命中；
    n=b+c；p=2·P(X≤min(b,c)), X~Bin(n,0.5)，截断 1（n=0 → p=1.0）。
    """
    shared = set(items_a) & set(items_b)
    b = sum(1 for k in shared if items_a[k] and not items_b[k])
    c = sum(1 for k in shared if items_b[k] and not items_a[k])
    n = b + c
    if n == 0:
        p = 1.0
    else:
        p_one = sum(comb(n, i) for i in range(min(b, c) + 1)) * (0.5 ** n)
        p = min(1.0, round(2 * p_one, 6))
    return {"b": b, "c": c, "n": n, "p": p}


def arm_stats(battles):
    """各臂聚合（rerun.aggregate 同风）：n/mean/min/max（recall 四位舍入）。"""
    out = {}
    for arm in (ARM_CONTROL, ARM_TREAT):
        rs = [b["recall"] for b in battles if b["arm"] == arm]
        if rs:
            out[arm] = {"n": len(rs), "mean": round(sum(rs) / len(rs), 4),
                        "min": min(rs), "max": max(rs)}
    return out


def pooled_mcnemar(battles):
    """池化配对：臂内任一战命中即命中（多战臂的逐 GT 池化口径）；
    单臂/无分母 → None（诚实降级，前端显示「未有两臂样本」）。"""
    pools = {}
    for arm in (ARM_CONTROL, ARM_TREAT):
        pool = {}
        for b in battles:
            if b["arm"] == arm:
                for gid, hit in b["per_item"].items():
                    pool[gid] = pool.get(gid, False) or bool(hit)
        pools[arm] = pool
    if not (pools[ARM_CONTROL] and pools[ARM_TREAT]):
        return None
    r = mcnemar_exact(pools[ARM_CONTROL], pools[ARM_TREAT])
    r["shared"] = len(set(pools[ARM_CONTROL]) & set(pools[ARM_TREAT]))
    if r["shared"] == 0:
        r["verdict"] = "无共有 GT 项，无法配对"
    elif r["p"] < 0.05:
        r["verdict"] = "显著差异（p<0.05）"
    else:
        r["verdict"] = "无显著差异（p≥0.05）"
    return r


def battles_metrics(battles_dir=None):
    """扫 battle-N 目录逐战装配（只读）：{battles:[{id,n,arm,recall,hits,total,
    missing,chain,per_item}], stats:{臂:聚合}, mcnemar:{b,c,n,p,shared,verdict}|None}。
    未结算（无 recall 行）/空目录/非 battle-N 一律跳过——多代格式容错降级。"""
    bdir = battles_dir or default_battles_dir()
    try:
        names = sorted(os.listdir(bdir))
    except OSError:
        names = []
    out = []
    for name in names:
        m = _BATTLE.match(name)
        if not m:
            continue
        home = os.path.join(bdir, name)
        try:
            with open(os.path.join(home, "settle-report.txt"),
                      encoding="utf-8", errors="replace") as f:
                settled = parse_settle(f.read())
        except OSError:
            continue
        if settled is None:
            continue
        missing = set(settled["missing"])
        out.append({"id": name, "n": int(m.group(1)), "arm": battle_arm(home),
                    "recall": settled["recall"], "hits": settled["hits"],
                    "total": settled["total"], "missing": settled["missing"],
                    "chain": settled["chain"],
                    "per_item": per_item_map(home, bdir, missing)})
    out.sort(key=lambda b: b["n"])
    return {"battles": out, "stats": arm_stats(out), "mcnemar": pooled_mcnemar(out)}


def metrics_view(battles_dir=None):
    """server /api/metrics.json 单源入口（_PAGE_API 挂载点；只读装配）；
    v0.9d 增 experiments 键——预登记实验登记处投影（度量页「预登记实验」小节同源）。"""
    out = battles_metrics(battles_dir)
    out["experiments"] = experiments_view()
    return out


# ---------------------------------------------------------------------------
# 实验登记处（v0.9d · 计划 2026-10-14-exp-registry R1/R2）——预登记纪律的只读投影。
# 格式律：experiments/<exp-id>.tsv，行式 field<TAB>value（11 字段，可 grep）；
# 预登记先落 tsv 再开战；判决后回填 verdict；无登记=度量页不认。
# ---------------------------------------------------------------------------

EXP_FIELDS = ("id", "question", "battles_control", "battles_treatment", "gt_gen",
              "decision_rule", "registered", "status", "verdict", "source", "note")


def default_repo_root():
    """仓库根=本文件（cli/webui/metrics.py）上三级——登记处挂 <repo>/experiments。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_exp_tsv(text):
    """登记 tsv 文本 → dict：field<TAB>value 行式；坏行（空/无制表符）跳过，
    重复字段后值覆盖；值两侧空白剥净（grep 友好的行式格式，多代降级）。"""
    out = {}
    for line in text.splitlines():
        if not line.strip() or "\t" not in line:
            continue
        field, value = line.split("\t", 1)
        field = field.strip()
        if field:
            out[field] = value.strip()
    return out


def experiments_view(repo_root=None):
    """实验登记处列表（只读，零写入）：<repo>/experiments/*.tsv 逐个解析 →
    规范化 dict 列表（11 字段齐、缺字段降级空串、按 id 升序）；
    无 id 的登记/非 .tsv 文件/无目录一律跳过（降级为空表，前端显示「无预登记实验」）。"""
    exp_dir = os.path.join(repo_root or default_repo_root(), "experiments")
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
                doc = parse_exp_tsv(f.read())
        except OSError:
            continue
        if not doc.get("id"):
            continue                                   # 无 id=坏登记，跳过
        out.append(dict((k, doc.get(k, "")) for k in EXP_FIELDS))
    out.sort(key=lambda e: e["id"])
    return out
