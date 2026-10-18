#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evals/gt/gt_eval.py — 会话 GT 评测跑（召回/误报基线面）。

复用 tests/eval_range_recall.py 的 load_session/score 单源（keying 随其常量走），
对 N 个账本会话出五列：recall=hits/gt_total；FP=活跃发现数−hits
（合成靶场全真值=GT：重复报告/诱饵面命中/幻觉发现皆计 FP）；precision=hits/活跃数。
用法：
  python3 evals/gt/gt_eval.py --session <dir> --label <名> [--gt <json>] ... [--write <tsv>] [--timestamp T]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "cli"))
from tests.eval_range_recall import load_session, score, KEYING_VERSION  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

GT_DEFAULT = os.path.join(REPO, "tests", "range", "ground-truth.json")


def eval_session(session_dir, gt_path):
    with open(gt_path, encoding="utf-8") as f:
        gt_doc = json.load(f)
    gt = gt_doc.get("planted", [])
    rows, cards = load_session(session_dir)
    recall, missing = score(rows, cards, gt_doc)
    hits = round(recall * len(gt))
    # 活跃发现数：status 列空或 active（与 scorer 同口径；列位=schemas TABLES 单源）
    si = TABLES["findings.tsv"].index("status")
    statuses = {}
    for r in rows["findings.tsv"]:
        st = r[si] if len(r) > si else ""
        statuses[st] = statuses.get(st, 0) + 1
    active = statuses.get("", 0) + statuses.get("active", 0)
    fp = max(0, active - hits)
    prec = (hits / active) if active else 0.0
    return {"gt_total": len(gt), "hits": hits, "recall": recall, "active_findings": active,
            "fp": fp, "precision": round(prec, 4), "missing": missing,
            "keying": KEYING_VERSION}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", action="append", required=True, help="会话目录（可多次）")
    ap.add_argument("--label", action="append", default=[], help="与会话一一对应的标签")
    ap.add_argument("--gt", default=GT_DEFAULT)
    ap.add_argument("--write", default=None, help="追加写基线 TSV")
    ap.add_argument("--timestamp", default="2026-10-19T00:00:00Z")
    a = ap.parse_args(argv)
    labels = a.label or [os.path.basename(s.rstrip("/")) for s in a.session]
    out = []
    for lbl, sess in zip(labels, a.session):
        r = eval_session(sess, a.gt)
        row = {"label": lbl, "session": sess, "gt": os.path.relpath(a.gt, REPO), "ran_at": a.timestamp, **{k: v for k, v in r.items() if k != "missing"}}
        out.append(row)
        print("EVAL\t%s\trecall=%.2f (%d/%d)\tfp=%d\tprecision=%.3f\tactive=%d\tkeying=v%s" % (
            lbl, r["recall"], r["hits"], r["gt_total"], r["fp"], r["precision"], r["active_findings"], r["keying"]))
    if a.write:
        cols = ("label", "session", "gt", "gt_total", "hits", "recall", "active_findings", "fp", "precision", "keying", "ran_at")
        exists = os.path.exists(a.write)
        os.makedirs(os.path.dirname(a.write), exist_ok=True)
        with open(a.write, "a", encoding="utf-8") as f:
            if not exists:
                f.write("# evals/gt/baselines — 会话 GT 评测基线（追加式；列见首行）\n")
                f.write("\t".join(cols) + "\n")
            for row in out:
                f.write("\t".join(str(row.get(c, "")) for c in cols) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
