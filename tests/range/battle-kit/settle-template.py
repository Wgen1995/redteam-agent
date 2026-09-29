#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G-r4 结算核验+评分一键驱动（主代理持有，战士交付后执行）。
步骤：①仓净核验（战士零仓库写入）②summary 契约形态 ③账本门禁/表完备 ④scorer。"""
import json, os, subprocess, sys

REPO = "/Users/wgen/redteam-agent"
GD = "/tmp/tanyin-range-battle/G-r4"
SUM = "/tmp/tanyin-range-battle/G-r4-summary.json"


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def main():
    print("== ① 仓净核验")
    rc, out, _e = sh("git status --porcelain", cwd=REPO)
    print("repo dirty lines:", len(out.splitlines()) if out else 0)
    if out:
        print(out[:400])
    print("== ② summary 契约")
    if not os.path.isfile(SUM):
        print("summary 缺失——战士未交付")
        sys.exit(1)
    s = json.load(open(SUM, encoding="utf-8"))
    det = s.get("detected", [])
    print("detected:", len(det), "auth_channel:", str(s.get("auth_channel"))[:60],
          "waves:", s.get("probe_waves"))
    bad = [d for d in det if not str(d.get("endpoint", "")).startswith("svc-")]
    print("非 canonical 键形:", len(bad))
    print("== ③ 账本完备")
    for t in ("goals.tsv", "findings.tsv", "E-index.tsv", "facts.tsv", "matrix.tsv", "timeline.tsv"):
        p = os.path.join(GD, t)
        n = sum(1 for _ in open(p, encoding="utf-8")) if os.path.isfile(p) else -1
        print(t, n)
    rc, out, _e = sh("grep -c gate: %s/timeline.tsv" % GD)
    print("gate 事件:", out)
    rc, out, _e = sh("grep -c replay: %s/timeline.tsv" % GD)
    print("replay 事件:", out)
    print("== ④ scorer（主代理专属）")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tests", "eval_range_recall.py"),
                        "--session", GD, "--ground-truth",
                        os.path.join(REPO, "tests", "range", "ground-truth.json")],
                       capture_output=True, text=True)
    print(r.stdout[:800])
    print("scorer rc=", r.returncode)


if __name__ == "__main__":
    main()
