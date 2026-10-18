#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evals/gt/gt_eval.py — 会话 GT 评测跑（召回/误报基线面）+ 链级两档判分（L3）。

复用 tests/eval_range_recall.py 的 load_session/score 单源（keying 随其常量走），
对 N 个账本会话出五列：recall=hits/gt_total；FP=活跃发现数−hits
（合成靶场全真值=GT：重复报告/诱饵面命中/幻觉发现皆计 FP）；precision=hits/活跃数。
链式面（--chain <battlefield.json>）：会话链（战场带 session_gt）逐链判分——步命中=
该 gt_ref 条目被单源 scorer 判命中；链级两档判分口径写死（CHAIN_TIERS 常量钉死，
禁漂移）：整链全对=1.0 / 部分对=0.5 / 零命中=0；chain_recall=Σ链分/链数；
同场输出 step_recall（环级平铺）与 flat_recall（全场 56 召回）作对照。
用法：
  python3 evals/gt/gt_eval.py --session <dir> --label <名> [--gt <json>] ...
      [--chain <battlefield.json>] ... [--write <tsv>] [--write-chain <tsv>] [--timestamp T]
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

# 链级两档判分口径（写死不漂——GT L3 链式扩容契约）：整链全对=1.0/部分对=0.5/零=0。
# 「部分对」=命中 ≥1 环但非全部环（断链位置不加分不扣分——两档之外无中间档）。
CHAIN_TIERS = {"full": 1.0, "partial": 0.5, "zero": 0.0}


def load_chain_battlefield(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    chains = [c for c in doc.get("chains", []) if c.get("polarity", "pos") == "pos"]
    return doc, chains


def score_chain(chain, hit_ids):
    """单链判分（纯函数面）。hit_ids=会话 GT 命中条目 id 集（score() 的 missing 取补）。
    返回 dict：tier/score/steps_hit/steps_total/missed_steps——口径=CHAIN_TIERS 两档。"""
    hits = [bool(s.get("gt_ref") and s["gt_ref"] in hit_ids) for s in chain["steps"]]
    n_hit = sum(hits)
    if n_hit == len(hits) and n_hit:
        tier = "full"
    elif n_hit:
        tier = "partial"
    else:
        tier = "zero"
    return {"chain_id": chain["id"], "steps_total": len(hits), "steps_hit": n_hit,
            "tier": tier, "score": CHAIN_TIERS[tier],
            "missed_steps": [s["gt_ref"] for s, h in zip(chain["steps"], hits) if not h]}


def chain_recall(chain_results):
    """链式召回=Σ链分/链数（半分链拖低均值的幅度=0.5/链数——两档压缩的度量面）。"""
    return (sum(r["score"] for r in chain_results) / len(chain_results)) if chain_results else 0.0


def eval_session_chains(session_dir, chain_path, gt_path=GT_DEFAULT):
    """会话链评测：单源 scorer 出命中集 → 逐链两档判分 + 三召回对照（链式/环级/全场）。"""
    doc, chains = load_chain_battlefield(chain_path)
    if not doc.get("session_gt"):
        raise ValueError("chain battlefield lacks session_gt (source-anchored → gt_verify, not session scoring): " + chain_path)
    with open(gt_path, encoding="utf-8") as f:
        gt_doc = json.load(f)
    gt_ids = {e.get("id") for e in gt_doc.get("planted", [])}
    rows, cards = load_session(session_dir)
    recall, missing = score(rows, cards, gt_doc)
    hit_ids = gt_ids - set(missing)
    results = [score_chain(c, hit_ids) for c in chains]
    steps_total = sum(r["steps_total"] for r in results)
    steps_hit = sum(r["steps_hit"] for r in results)
    missed, seen = [], set()
    for r in results:
        for m in r["missed_steps"]:
            if m not in seen:
                seen.add(m)
                missed.append(m)
    return {"chain_battlefield": doc.get("battlefield"), "chains": len(results),
            "full": sum(1 for r in results if r["tier"] == "full"),
            "partial": sum(1 for r in results if r["tier"] == "partial"),
            "zero": sum(1 for r in results if r["tier"] == "zero"),
            "chain_recall": chain_recall(results), "chain_results": results,
            "steps_total": steps_total, "steps_hit": steps_hit,
            "step_recall": (steps_hit / steps_total) if steps_total else 0.0,
            "flat_recall": recall, "missed_steps": missed, "keying": KEYING_VERSION}


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
    ap.add_argument("--chain", action="append", default=[],
                    help="链式战场 JSON（会话链；可多次——源码链走 gt_verify 不在此判分）")
    ap.add_argument("--write", default=None, help="追加写基线 TSV")
    ap.add_argument("--write-chain", dest="write_chain", default=None, help="追加写链式基线 TSV")
    ap.add_argument("--timestamp", default="2026-10-19T00:00:00Z")
    a = ap.parse_args(argv)
    labels = a.label or [os.path.basename(s.rstrip("/")) for s in a.session]
    out = []
    chain_out = []
    for lbl, sess in zip(labels, a.session):
        r = eval_session(sess, a.gt)
        row = {"label": lbl, "session": sess, "gt": os.path.relpath(a.gt, REPO), "ran_at": a.timestamp, **{k: v for k, v in r.items() if k != "missing"}}
        out.append(row)
        print("EVAL\t%s\trecall=%.2f (%d/%d)\tfp=%d\tprecision=%.3f\tactive=%d\tkeying=v%s" % (
            lbl, r["recall"], r["hits"], r["gt_total"], r["fp"], r["precision"], r["active_findings"], r["keying"]))
        for cp in a.chain:
            cr = eval_session_chains(sess, cp, a.gt)
            score_sum = sum(x["score"] for x in cr["chain_results"])
            print("CHAIN\t%s\tchains=%d\tfull=%d\tpartial=%d\tzero=%d\tchain_recall=%.2f (%g/%d)"
                  "\tstep_recall=%.2f (%d/%d)\tflat_recall=%.2f" % (
                      lbl, cr["chains"], cr["full"], cr["partial"], cr["zero"],
                      cr["chain_recall"], score_sum, cr["chains"],
                      cr["step_recall"], cr["steps_hit"], cr["steps_total"], cr["flat_recall"]))
            for x in cr["chain_results"]:
                print("CHAIN-TIER\t%s\t%s\tsteps=%d/%d\tmissed=%s" % (
                    x["chain_id"], x["tier"], x["steps_hit"], x["steps_total"],
                    ",".join(x["missed_steps"]) or "-"))
            chain_out.append({"label": lbl, "session": sess,
                              "chain_battlefield": cr["chain_battlefield"],
                              **{k: v for k, v in cr.items() if k not in ("chain_results", "chain_battlefield")},
                              "missed_steps": ",".join(cr["missed_steps"]),
                              "ran_at": a.timestamp})
    if a.write_chain:
        cols = ("label", "session", "chain_battlefield", "chains", "full", "partial", "zero",
                "chain_recall", "step_recall", "flat_recall", "missed_steps", "keying", "ran_at")
        exists = os.path.exists(a.write_chain)
        os.makedirs(os.path.dirname(a.write_chain), exist_ok=True)
        with open(a.write_chain, "a", encoding="utf-8") as f:
            if not exists:
                f.write("# evals/gt/baselines — 链式召回基线（追加式；两档判分=CHAIN_TIERS 写死；列见首行）\n")
                f.write("\t".join(cols) + "\n")
            for row in chain_out:
                vals = [(" %.2f" % row[c]).strip() if c in ("chain_recall", "step_recall", "flat_recall")
                        else str(row.get(c, "")) for c in cols]
                f.write("\t".join(vals) + "\n")
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
