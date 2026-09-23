# -*- coding: utf-8 -*-
"""黄金回归总驱动（批次 1 T13）——41 命令全覆盖。"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli", "tanyin-ledger")
FIX = os.path.join(HERE, "fixtures", "G-g1")
GOLD = os.path.join(HERE, "golden")
TS = "2026-09-23T07:00:00Z"
A64 = "a" * 64

READ_CMDS = [
    ["validate"], ["verify-chain"], ["next-id", "intents", "INT", "g1"],
    ["unconsumed-facts"], ["pending-intents"], ["matrix-gaps"],
    ["converge-check"], ["intent-status", "INT-g1-0001"], ["matrix-get", "web.admin-panel"],
    ["scope-check", "shop.example"], ["budget-check"], ["cleanup-checklist"],
    ["hash-recheck"], ["matrix-audit"], ["state-rebuild"], ["set-replay-state", "status"],
    ["ledger-scope-coverage"], ["ledger-tree-check"], ["ledger-replay-summary"],
    ["ledger-terminal-gate"], ["redact-scan"],
]

WRITE_CMDS = ["add-goal", "add-scope", "add-intent", "set-intent-status", "add-fact",
              "add-finding", "supersede-finding", "add-asset", "add-cred", "set-cred-status",
              "add-edge", "add-evidence", "amend-scope", "matrix-set", "matrix-freeze",
              "append-timeline", "approve", "budget-log", "checkpoint", "matrix-init"]

VALS = {
    "--target": "shop2.example", "--objective": "回归目标", "--auth-doc": "auth/g.pdf",
    "--auth-sha256": A64, "--signer": "client-cso", "--valid-from": "2026-09-01",
    "--valid-until": "2026-09-30", "--budget": "1M;1000;10", "--model-tier": "strong",
    "--guard-tier": "T3", "--timestamp": TS, "--matcher": "api.shop.example",
    "--note": "golden", "--account": "admin", "--title": "回归意图",
    "--detail": "回归明细", "--engine": "web-blackbox",
    "--score": "0.5", "--via": "CNPEN-SD-01", "--dedup-key": "golden-key",
    "--budget-share": "0.1", "--id": "INT-g1-0002", "--status": "active",
    "--intent-id": "INT-g1-0001", "--confidence": "C3", "--impact": "中",
    "--description-brief": "回归描述", "--type": "subdomain", "--value": "api.shop.example",
    "--role": "operator", "--username-ref": "op1", "--secret-ref": "{{vault:cred-2}}",
    "--scope-asset": "AST-g1-0002", "--permitted-actions": "read",
    "--source-id": "F-g1-0001", "--target-id": "INT-g1-0001",
    "--network-position": "internet", "--repro-command": "curl -s https://api.shop.example/x",
    "--repro-kind": "single", "--content-hash-raw": "c" * 64, "--content-hash-norm": "d" * 64,
    "--amendment-of": "S-g1-0001", "--attack-surface": "web.api", "--vuln-class": "inj.sql",
    "--state": "?", "--reason": "golden", "--actor": "CLI", "--phase": "P3",
    "--event": "golden-event", "--revert-cmd": "", "--command-hash": "b" * 64,
    "--decision": "approved", "--approver": "user", "--token-delta": "100",
    "--requests-delta": "1", "--hours-delta": "0.1", "--dollars-delta": "0",
    "--scope": "goal", "--finding-id": "FD-g1-0001", "--evidence-id": "EV-g1-0001",
    "--observed-at": TS, "--session": "golden-s",  # 批次 3 T4：checkpoint --session 必填
}
KIND_BY_CMD = {"add-scope": "include", "add-cred": "static-cred", "add-intent": "recon",
               "add-fact": "info", "add-edge": "spawns"}


def run_cli(gd, name, args):
    return subprocess.run([sys.executable, CLI, name, "--goal-dir", gd] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


# 批次 3 T2：tanyin-phases 确定性面（无 goal-dir，读仓库 phases/phases.yaml）——金样走同一机制
PHASES_CLI = os.path.join(HERE, "..", "cli", "tanyin-phases")
PHASES_CMDS = [["validate"]]


def run_phases(args):
    return subprocess.run([sys.executable, PHASES_CLI] + args,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def fresh(tmp):
    d = os.path.join(tmp, "G-g1")
    if os.path.exists(d):
        shutil.rmtree(d)
    return shutil.copytree(FIX, d)


OVERRIDE = {
    "add-intent": {"--origin": "entity", "--budget-share": "100;10;1"},
    "add-fact": {"--confidence": "0.9"},
    "add-finding": {"--exploitation-status": "suspected", "--scope-check": "in_scope",
                    "--affected-asset-id": "AST-g1-0002", "--evidence-ids": "EV-g1-0001"},
    "supersede-finding": {"--id": "FD-g1-0002", "--superseded-by": "FD-g1-0001"},
    "add-edge": {"--kind": "proves", "--source-id": "INT-g1-0001", "--target-id": "FD-g1-0001",
                 "--provenance": "P3"},
    "add-evidence": {"--source-type": "command"},
    "amend-scope": {"--kind": "include", "--approval": "AP-g1-0001"},
    "matrix-freeze": {},
}
PRE_OPS = {"supersede-finding": [["@craft-supersede"]]}
FIXTURE_PREP = {"add-goal": ["goals.tsv"]}


def autodrive(name, gd):
    for op in PRE_OPS.get(name, []):
        if op[0] == "@craft-supersede":
            sys.path.insert(0, os.path.join(HERE, "..", "cli"))
            from ledger.core import esc, unesc
            from ledger.schemas import TABLES
            p = os.path.join(gd, "findings.tsv")
            rows = [[unesc(c) for c in l.split(chr(9))] for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
            si = TABLES["findings.tsv"].index("status")
            ki = TABLES["findings.tsv"].index("dedup_key")
            rows[0][si] = "active"
            r2 = list(rows[0])
            r2[0] = "FD-g1-0002"
            r2[ki] = rows[0][ki]
            rows.append(r2)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(chr(10).join(chr(9).join(esc(c) for c in r) for r in rows) + chr(10))
        else:
            run_cli(gd, op[0], op[1:])
    if name == "matrix-freeze":  # 预解冻：清全部 frozen_at，冻结盖戳才可正例
        p = os.path.join(gd, "matrix.tsv")
        lines = [l.split(chr(9)) for l in open(p, encoding="utf-8").read().splitlines() if l.strip()]
        for r in lines:
            if len(r) >= 8:
                r[7] = ""
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(chr(10).join(chr(9).join(r) for r in lines) + chr(10))
    for kill in FIXTURE_PREP.get(name, []):
        p = os.path.join(gd, kill)
        if os.path.exists(p):
            os.remove(p)
    ov = OVERRIDE.get(name, {})
    args = ["--timestamp=" + TS] + [k + "=" + v for k, v in ov.items()]
    if name == "matrix-init":
        open(os.path.join(gd, "matrix.tsv"), "w", encoding="utf-8").close()
    r = None
    for _ in range(12):
        r = run_cli(gd, name, args)
        m = re.search("必填参数缺失或为空: (--[a-z0-9-]+)", r.stdout + r.stderr)
        if not m:
            return args, r
        p = m.group(1)
        v = OVERRIDE.get(name, {}).get(p, VALS.get(p))
        if p == "--kind":
            v = KIND_BY_CMD.get(name, "info")
        if v is None:
            v = "x"
        args.append(p + "=" + v)
    return args, r


def norm_read(text):
    ts = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
    return ts.sub("TS", text).strip()


def norm_state(gd):
    ts = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
    parts = []
    for t in sorted(os.listdir(gd)):
        if not os.path.isfile(os.path.join(gd, t)):
            continue
        body = open(os.path.join(gd, t), encoding="utf-8").read()
        parts.append("== " + t + " ==")
        parts.extend(sorted(ts.sub("TS", l) for l in body.splitlines() if l.strip()))
    return chr(10).join(parts)


def main():
    fails, inits = [], []
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        for spec in READ_CMDS:
            name = spec[0]
            a1 = run_cli(FIX, name, spec[1:])
            gd2 = fresh(t2)
            a2 = run_cli(gd2, name, spec[1:])
            o1, o2 = norm_read(a1.stdout), norm_read(a2.stdout)
            if o1 != o2:
                fails.append(name + "(不确定性)")
                continue
            gp = os.path.join(GOLD, "read-" + name + ".norm")
            if not os.path.exists(gp):
                with open(gp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(o1)
                inits.append(name)
            elif open(gp, encoding="utf-8").read().strip() != o1:
                fails.append(name + "(输出漂移)")
        for name in WRITE_CMDS:
            outs = []
            for t in (t1, t2):
                gd = fresh(t)
                args, r = autodrive(name, gd)
                outs.append((args, r.returncode, norm_state(gd), norm_read(r.stdout)))
            (args, rc, s1, o1) = outs[0]
            (_, _, s2, o2) = outs[1]
            if rc != 0:
                fails.append(name + "(驱动未收敛 rc=%d)" % rc)
                continue
            if s1 != s2:
                fails.append(name + "(状态不确定性)")
                continue
            gp = os.path.join(GOLD, "write-" + name + ".state")
            if not os.path.exists(gp):
                with open(gp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(o1 + chr(10) + s1)
                inits.append(name)
            elif open(gp, encoding="utf-8").read().strip() != (o1 + chr(10) + s1).strip():
                fails.append(name + "(状态漂移)")
        for spec in PHASES_CMDS:
            a1 = run_phases(spec)
            a2 = run_phases(spec)
            o1, o2 = norm_read(a1.stdout), norm_read(a2.stdout)
            if a1.returncode != 0 or o1 != o2:
                fails.append("phases-" + spec[0] + "(不确定性或非零退出)")
                continue
            gp = os.path.join(GOLD, "phases-" + spec[0] + ".norm")
            if not os.path.exists(gp):
                with open(gp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(o1)
                inits.append("phases-" + spec[0])
            elif open(gp, encoding="utf-8").read().strip() != o1:
                fails.append("phases-" + spec[0] + "(输出漂移)")
    for n in inits:
        print("INIT " + n)
    if fails:
        for f in fails:
            print("FAIL " + f)
        return 1
    print("PASS golden: %d 读面 + %d 写面 + %d phases 面 全部锁定且确定"
          % (len(READ_CMDS), len(WRITE_CMDS), len(PHASES_CMDS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
