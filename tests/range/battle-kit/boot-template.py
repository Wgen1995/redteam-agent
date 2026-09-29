#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G-r3 开账驱动（P0-P1）：靶场第二轮亲自作战。仓外执行，仓库零写。"""
import os, subprocess, sys

REPO = "/Users/wgen/redteam-agent"
GD = "/tmp/tanyin-range-battle/G-r3"
LEDGER = os.path.join(REPO, "cli", "tanyin-ledger")


def led(*args):
    r = subprocess.run([sys.executable, LEDGER, args[0], "--goal-dir", GD] + list(args[1:]),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tag = args[0] if args else "?"
    if r.returncode != 0:
        print("!! %s rc=%d\n%s%s" % (tag, r.returncode, r.stdout[-400:], r.stderr[-400:]))
        sys.exit(1)
    return r.stdout


def main():
    os.makedirs(GD, exist_ok=True)
    T = lambda n: "2026-09-27T13:%02d:00Z" % n
    led("add-goal", "--target=authorized-range.local", "--objective=靶场第二轮在环复测（基线 v2）",
        "--auth-doc=AUTH-RANGE-2026-09-27.pdf", "--auth-sha256=" + "a" * 64,
        "--signer=range-operator", "--valid-from=2026-09-27T00:00:00Z",
        "--valid-until=2026-09-28T00:00:00Z", "--budget=2M;50000;40",
        "--model-tier=strong", "--guard-tier=T3", "--timestamp=" + T(0))
    led("add-scope", "--kind=include", "--matcher=*.range.local", "--timestamp=" + T(1))
    led("add-scope", "--kind=include", "--matcher=172.28.0.0/24", "--timestamp=" + T(1))
    # 批次 10（缝⑩收口）：八服务名单标签显式 include——scope 执法面与键形 v3 对齐
    # （否则 svc-* 资产/端点全数误判 out_of_scope，add-finding 联查断言拒收）
    for svc in ("svc-shop", "svc-api-gw", "svc-admin", "svc-login",
                "svc-billing", "svc-dashboard", "svc-portal", "svc-files"):
        led("add-scope", "--kind=include", "--matcher=" + svc, "--timestamp=" + T(1))
    led("add-scope", "--kind=exclude", "--matcher=*.out-of-scope.local", "--timestamp=" + T(1))
    led("add-scope", "--kind=oob", "--matcher=192.168.0.0/16", "--timestamp=" + T(1))
    eg = subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-egress"),
                         "compile", "--goal-dir", GD, "--timestamp=2026-09-27T08:00:00Z"],
                        capture_output=True, text=True)
    print("egress rc=%d" % eg.returncode)
    if eg.returncode != 0:
        print(eg.stderr[-300:]); sys.exit(1)
    led("add-asset", "--type=root-domain", "--value=range.local",
        "--meta=靶场授权域", "--timestamp=" + T(2))
    root_id = "AST-r3-0001"
    for i, s in enumerate(("svc-shop", "svc-api-gw", "svc-admin", "svc-login", "svc-billing",
                           "svc-dashboard", "svc-portal", "svc-files")):
        led("add-asset", "--type=service", "--value=" + s,
            "--meta=靶场内网服务", "--timestamp=" + T(3 + i))
        led("add-edge", "--kind=parent", "--source-id=AST-r3-%04d" % (i + 2),
            "--target-id=" + root_id, "--provenance=range-runbook",
            "--timestamp=" + T(3 + i))
    ph = subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-phases"),
                         "gate", "--goal-dir", GD, "--phase=P0", "--timestamp=" + T(1)],
                        capture_output=True, text=True)
    print("P0 rc=%d" % ph.returncode)
    print(ph.stdout[-200:], ph.stderr[-200:])
    ph = subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-phases"),
                         "gate", "--goal-dir", GD, "--phase=P1", "--timestamp=" + T(12)],
                        capture_output=True, text=True)
    print("P1 rc=%d" % ph.returncode)
    print(ph.stdout[-300:], ph.stderr[-200:])
    led("matrix-init", "--timestamp=" + T(13))
    dr = subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-phases"),
                         "denominator-ready", "--goal-dir", GD], capture_output=True, text=True)
    print("denominator-ready rc=%d %s" % (dr.returncode, dr.stdout[-120:]))
    led("matrix-freeze", "--timestamp=" + T(14))
    ph = subprocess.run([sys.executable, os.path.join(REPO, "cli", "tanyin-phases"),
                         "gate", "--goal-dir", GD, "--phase=P2", "--timestamp=" + T(15)],
                        capture_output=True, text=True)
    print("P2 rc=%d" % ph.returncode)
    print(ph.stdout[-250:], ph.stderr[-200:])


if __name__ == "__main__":
    main()
