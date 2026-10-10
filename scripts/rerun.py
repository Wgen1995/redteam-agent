#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rerun · v0.5b G3 干净重跑协议（autotest 专家项）——n=1 叙事→统计面。

同任务书+同字典 N>=3 战：settle 报告 recall 行聚合（mean/std/min/max）。
用法：
  python3 scripts/rerun.py --reports <settle-report.txt>...     # 聚合既有
  python3 scripts/rerun.py --dry                                # 假报告走全链（自检）
真战编排（init/launch/settle xN）由 RUNBOOK 驱动——本脚本只做「干净聚合」，
不代跑战斗（同 scorer 不代跑代理的边界律）。
"""
import argparse
import re
import statistics
import sys

_RECALL = re.compile(r"recall=([0-9.]+) \((\d+)/(\d+)\)")


def parse_recall(text):
    """从 settle 报告文本抽首个 recall 行 → (score, hit, total)；无 → None。"""
    m = _RECALL.search(text)
    return (float(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def aggregate(scores):
    """聚合：n/mean/std(样本)/min/max；n<2 std=None。"""
    if not scores:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    return {
        "n": len(scores),
        "mean": round(statistics.mean(scores), 4),
        "std": round(statistics.stdev(scores), 4) if len(scores) > 1 else None,
        "min": min(scores),
        "max": max(scores),
    }


def verdict(n):
    """诚实措辞：n=1 显式无统计效力（RT-0023 教训）；n>=3 给统计面。"""
    if n <= 0:
        return "无有效样本（settle 报告缺 recall 行？）"
    if n == 1:
        return "单样本（n=1 无统计效力，RT-0023 教训）"
    return "n=%d 统计面：见 mean/std（>=3 方可谈稳定性；显著性另需 McNemar，v0.6）" % n


def mcnemar_exact(b, c):
    """v0.6 H3：精确 McNemar（双尾二项）——b=仅新战命中，c=仅旧战命中。"""
    n = b + c
    if n == 0:
        return 1.0
    from math import comb
    k = min(b, c)
    p_one = sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, round(2 * p_one, 6))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rerun.py")
    ap.add_argument("--reports", nargs="*", default=[], help="settle-report.txt 路径列表")
    ap.add_argument("--dry", action="store_true", help="假报告自检全链")
    a = ap.parse_args(argv)
    texts = []
    if a.dry:
        texts = ["verify-chain: PASS\nrecall=0.66 (37/56)\n",
                 "verify-chain: PASS\nrecall=0.62 (35/56)\n",
                 "verify-chain: PASS\nrecall=0.57 (32/56)\n"]
        print("[dry] 三份假报告走全链")
    else:
        for p in a.reports:
            with open(p, encoding="utf-8", errors="replace") as f:
                texts.append(f.read())
    scores, hits, totals = [], [], []
    for t in texts:
        r = parse_recall(t)
        if r:
            scores.append(r[0])
            hits.append(r[1])
            totals.append(r[2])
    agg = aggregate(scores)
    print("reports=%d parsed=%d denominator=%s" % (
        len(texts), agg["n"], ",".join(str(t) for t in sorted(set(totals))) or "-"))
    if agg["n"]:
        print("scores=%s" % ",".join(str(s) for s in scores))
        print("mean=%.4f std=%s min=%.2f max=%.2f" % (
            agg["mean"], agg["std"] if agg["std"] is not None else "n/a",
            agg["min"], agg["max"]))
    print("verdict: %s" % verdict(agg["n"]))
    return 0 if agg["n"] else 1


if __name__ == "__main__":
    sys.exit(main())
