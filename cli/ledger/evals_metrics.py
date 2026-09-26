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


# ------------------------------------------------- 批次 6 T2：静态 runner 接入
import subprocess
import tempfile

from ledger import evals_dual_anchor  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV = {**os.environ, "PYTHONUTF8": "1"}


def _runner_unittest(ctx):
    mods = ctx["args"]
    r = subprocess.run([sys.executable, "-m", "unittest"] + mods,
                       capture_output=True, text=True, timeout=600, cwd=_REPO, env=_ENV)
    return {"status": "PASS" if r.returncode == 0 else "FAIL", "actual": "rc=%d" % r.returncode}


register("unittest")(_runner_unittest)


@register("golden")
def _golden(ctx):
    # R-T1-1：tests/run_golden.py 为脚本非 unittest 模块——子进程实跑（防空绿假 PASS）
    r = subprocess.run([sys.executable, os.path.join("tests", "run_golden.py")],
                       capture_output=True, text=True, timeout=900, cwd=_REPO, env=_ENV)
    return {"status": "PASS" if r.returncode == 0 else "FAIL", "actual": "rc=%d" % r.returncode}


@register("report-scan")
def _report_scan(ctx):
    """M10：tempfile 最小会话→泄漏样本被 redact-scan 拦截→脱敏零泄漏→validate PASS。

    步骤任一不符=FAIL（actual 落步骤名）；文件/进程级 OSError 经 _one 转 ENV-SKIP。"""
    ts = "2026-09-24T00:00:00Z"
    with tempfile.TemporaryDirectory() as td:
        gd = os.path.join(td, "g")
        os.makedirs(gd)  # goal 目录须先在（core 纪律：不代建）

        def led(*args):
            return subprocess.run([sys.executable, os.path.join(_REPO, "cli", "tanyin-ledger"),
                                   args[0], "--goal-dir", gd] + list(args[1:]),
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=120, env=_ENV)
        r = led("add-goal", "--target=shop.example", "--objective=M10 扫描回归",
                "--auth-doc=auth/m10.md", "--auth-sha256=" + "a" * 64, "--signer=evals",
                "--valid-from=2026-09-01", "--valid-until=2026-09-30",
                "--budget=1M;1000;10", "--model-tier=strong", "--guard-tier=T3",
                "--timestamp=" + ts)
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "add-goal rc=%d" % r.returncode}
        r = led("add-scope", "--kind=include", "--matcher=shop.example", "--timestamp=" + ts)
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "add-scope rc=%d" % r.returncode}
        draft = os.path.join(td, "draft.md")
        with open(draft, "w", encoding="utf-8", newline="\n") as f:
            f.write("# 草稿\ntoken=sk-live-abc123\n")
        r = led("redact-scan", "--target=" + draft)
        if r.returncode == 0:
            return {"status": "FAIL", "actual": "泄漏样本未被拦截(redact-scan rc=0)"}
        if r.returncode not in (0, 1):
            return {"status": "FAIL", "actual": "redact-scan rc=%d（用法/环境）" % r.returncode}
        with open(draft, "w", encoding="utf-8", newline="\n") as f:
            f.write("# 草稿\ntoken=<redacted>\n")
        r = led("redact-scan", "--target=" + draft)
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "脱敏文本误报 rc=%d" % r.returncode}
        r = led("validate")
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "validate rc=%d" % r.returncode}
        return {"status": "PASS", "actual": "leak-blocked+clean-zero+validate-ok"}


@register("dual-anchor")
def _dual_anchor(ctx):
    """M12（裁决 E）：args=[approvals.tsv 路径, log.md 路径]（相对 goal_dir）。

    两 missing 清单皆空=PASS（actual 带 matched 计数）；文件缺=OSError→ENV-SKIP。"""
    ap_rel, log_rel = ctx["args"][0], ctx["args"][1]
    with open(os.path.join(ctx["goal_dir"], ap_rel), encoding="utf-8") as f:
        rows = [ln.rstrip("\r\n").split("\t") for ln in f if ln.strip()]
    with open(os.path.join(ctx["goal_dir"], log_rel), encoding="utf-8") as f:
        log_text = f.read()
    res = evals_dual_anchor.check(rows, log_text)
    if res["missing_in_ledger"] or res["missing_in_knowledge"]:
        return {"status": "FAIL", "actual": json.dumps(res, ensure_ascii=False)}
    return {"status": "PASS", "actual": "matched=%d" % len(res["matched"])}


# ------------------------------------------------- 批次 6 T3：动态 runner 接入
from ledger import evals_token_eff  # noqa: E402


def _read_tsv(path):
    # 仓库既有 TSV 读取惯例（同 dual-anchor 面）：tab 分隔、剥行尾、跳空行
    with open(path, encoding="utf-8") as f:
        return [ln.rstrip("\r\n").split("\t") for ln in f if ln.strip()]


@register("canary-zero")
def _canary_zero(ctx):
    """M03：逐档 probe（--tier=KV 形态）；rc=1=诱饵放行=零容忍 FAIL。

    rc=2=诱饵未部署（缺 canary/targets.tsv=环境前置缺）→ENV-SKIP（R-T3-3，
    以计划测试 assertIn(PASS, ENV-SKIP) 为准）；probe 未部署态不落账（零写热）。"""
    tiers = ctx["args"] or ["0", "1", "2", "3"]
    rc0 = 0
    for t in tiers:
        r = subprocess.run([sys.executable, os.path.join(_REPO, "cli", "tanyin-canary"), "probe",
                            "--goal-dir", ctx["goal_dir"], "--tier=" + t, "--timestamp=" + ctx["ts"]],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=120, cwd=_REPO, env=_ENV)
        if r.returncode == 2:
            return {"status": "ENV-SKIP",
                    "actual": "tier=%s 诱饵未部署（缺 canary/targets.tsv，先 deploy）" % t}
        if r.returncode != 0:
            return {"status": "FAIL", "actual": "tier=%s rc=%d（零容忍触碰）" % (t, r.returncode)}
        rc0 += 1
    return {"status": "PASS", "actual": "tiers=%d rc0=%d" % (len(tiers), rc0), "candidates": 0}


@register("replay-rate")
def _replay_rate(ctx):
    """M02：ledger-replay-summary 单源三态分布→replay_verdict 裁决（R-T3-2 映射）。

    VERIFIED→reproduced／REPAIRED→env-diff（已降级处置）／REJECTED→not-reproduced
    （未处置）；rc=1=有待重放项→FAIL；rc=2=ENV。"""
    r = subprocess.run([sys.executable, os.path.join(_REPO, "cli", "tanyin-ledger"),
                        "ledger-replay-summary", "--goal-dir", ctx["goal_dir"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=300, cwd=_REPO, env=_ENV)
    if r.returncode == 2:
        raise EnvironmentError("replay-summary ENV")
    if r.returncode != 0:
        return {"status": "FAIL",
                "actual": "ledger-replay-summary rc=%d（有待重放/REJECTED 未处置）" % r.returncode}
    kv = {}
    for part in r.stdout.strip().split("\t")[1:]:
        k, _, v = part.partition("=")
        kv[k] = int(v) if v.strip().isdigit() else 0
    states = (["reproduced"] * kv.get("verified", 0)
              + ["env-diff"] * kv.get("repaired", 0)
              + ["not-reproduced"] * kv.get("rejected", 0))
    verdict, counts = evals_token_eff.replay_verdict(states)
    return {"status": verdict, "actual": json.dumps(counts, ensure_ascii=False, sort_keys=True)}


@register("token-usage")
def _token_usage(ctx):
    """M05（裁决 G 校准通道）：timeline usage 行实采→比值→校准报告落 tests/evals/calib/。

    timeline.tsv 缺=OSError、无 usage 行=EnvironmentError（CI 干跑）→均 ENV-SKIP；
    真跑首采归 Task 17 靶场演练。"""
    rows = _read_tsv(os.path.join(ctx["goal_dir"], "timeline.tsv"))
    ratios = evals_token_eff.extract_ratios(rows)
    calib_dir = os.path.join(_REPO, "tests", "evals", "calib")
    os.makedirs(calib_dir, exist_ok=True)
    rep = evals_token_eff.write_calibration(ratios, os.path.join(calib_dir, "token-calibration.json"))
    return {"status": "PASS", "actual": "median=%.3f n=%d" % (rep["median"], rep["n"])}


@register("manual")
def _manual(ctx):
    """L3 对齐专用：恒 ENV-SKIP（设计 §9.3 发布前人工项不阻塞 CI；契约 15 §4 R-T1-2）。"""
    return {"status": "ENV-SKIP", "actual": "L3 发布前人工对齐（设计 §9.3 不阻塞 CI）"}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
