# -*- coding: utf-8 -*-
"""evals 运行器裁决引擎（退出码 0/1/2，裁决 A；runner 注册表单源）。

0=本套全部硬门 PASS；1=任一硬门 FAIL；2=存在 ENV-SKIP 且无硬门 FAIL 且无 PASS
（全 skip 才 2；部分 skip+有 PASS=0 并在 counts 披露）。warn 门 FAIL 不影响退出码。
时间戳一律显式字面量（禁墙钟，evals 可重放纪律）。"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger.evals_schema import load_metrics  # noqa: E402

EXIT_PASS, EXIT_GATE_FAIL, EXIT_ENV = 0, 1, 2
_RUNNERS = {}


def register(metric_id):
    def deco(fn):
        _RUNNERS[metric_id] = fn
        return fn
    return deco


def _one(m, goal_dir, ts):
    fn = _RUNNERS.get(m["source"]["runner"])
    if fn is None:
        return {"id": m["id"], "status": "ENV-SKIP", "actual": "runner 未注册: %s" % m["source"]["runner"]}
    try:
        r = fn({"goal_dir": goal_dir, "args": m["source"]["args"], "ts": ts, "metric": m})
    except EnvironmentError as e:  # openssl/docker 缺等环境前置（py3 中=OSError 同族）
        return {"id": m["id"], "status": "ENV-SKIP", "actual": "env: %s" % e}
    r.setdefault("id", m["id"])
    r.setdefault("baseline", m["baseline"]["value"])
    return r


def run_suite(metrics, suite, goal_dir, out_path=None, ts="2026-09-24T00:00:00Z"):
    ids = metrics["suites"][suite]
    by_id = {m["id"]: m for m in metrics["metrics"]}
    results, counts = [], {"pass": 0, "fail": 0, "warn_fail": 0, "env_skip": 0, "candidates": 0}
    for mid in ids:
        m = by_id[mid]
        r = _one(m, goal_dir, ts)
        results.append(r)
        if r["status"] == "PASS":
            counts["pass"] += 1
        elif r["status"] == "ENV-SKIP":
            counts["env_skip"] += 1
        elif m["gate"] == "warn":
            counts["warn_fail"] += 1
            r["status"] = "WARN-FAIL"
        else:
            counts["fail"] += 1
    counts["candidates"] = sum(int(r.get("candidates") or 0) for r in results)
    hard_fail = counts["fail"] > 0
    code = EXIT_GATE_FAIL if hard_fail else (EXIT_ENV if counts["pass"] == 0 else EXIT_PASS)
    report = {"format_version": 1, "suite": suite, "started_at": ts,
              "results": results, "counts": counts, "exit": code}
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    return code, report


def main(argv):
    ap = argparse.ArgumentParser(prog="tanyin-evals")
    ap.add_argument("cmd", choices=["run", "list", "report"])
    ap.add_argument("--metrics", default=os.path.join("tests", "evals", "metrics-v1.json"))
    ap.add_argument("--suite", default="static")
    ap.add_argument("--goal-dir", default=".")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "list":
        m = load_metrics(a.metrics)
        for x in m["metrics"]:
            print("%s [%s/%s/%s] %s" % (x["id"], x["layer"], x["gate"], x["kind"], x["title"]))
        return 0
    ts = a.timestamp or "2026-09-24T00:00:00Z"
    code, rep = run_suite(load_metrics(a.metrics), a.suite, a.goal_dir, a.out, ts)
    print(json.dumps(rep["counts"], ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
