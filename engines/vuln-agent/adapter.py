#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vuln-agent 适配器（批4 T9，契约 08 §5）——.vuln_agent_output→统一提交 schema。

--run：OS 参数化启动（POSIX python3 run.py / Windows python run.py，cwd=<source>）；
缺省=归一化既有输出（离线/测试）。归一化表=VERSION_MAP v1（版本差异容错：后续版本
新增字段在此映射，不改提交 schema）。引擎不写账本（单写者）。

POC 四要素门（FD 报告卡规格 2026-09-24 b0006f2 §一.6/§三——外部发现强制）：
vuln_findings 每条须含 raw_request/raw_response/时间/环境 四段，缺一即降级 fact
（kind=vuln-clue）不成 finding。四要素随提交携带：raw_request/raw_response 原文进
reproducible_steps（Burp 直贴可重放）、时间随 evidence_refs（源文件@时间戳）、
环境=network_position（vuln-agent 源码只读分析恒 same-host，G-19 视角标注载体）。"""
import json, os, re, subprocess, sys

RUN_PY = {"win32": "python", "posix": "python3"}
CONF_MAP = {"VULN": "C2", "SUSPECTED": "C3"}          # NOVULN→fact(kind=info)
SEVERITY_MAP = {"高": "高", "中": "中", "低": "低"}
POC_FIELDS = ("raw_request", "raw_response", "时间", "环境")


def _block(text, marker):
    """marker 行之后的 4 空格缩进块原文（Payload/raw_request/raw_response 同型）。"""
    m = re.search(r"\*\*" + marker + r"\*\*：?\n((?:    .*\n?)+)", text)
    if not m:
        return ""
    return "\n".join(l[4:].rstrip() for l in m.group(1).splitlines() if l.strip())


def _field(text, marker):
    """**marker**：值（同行内取到下一个 * 或行尾——兼容引擎合并行字段布局）。"""
    m = re.search(r"\*\*" + marker + r"\*\*：\s*([^*\n]+)", text)
    return m.group(1).strip() if m else ""


def parse_finding(path):
    """从 vuln_findings/*.md 提取类型/位置/CVSS/严重性/Payload+POC 四要素（确定性正则）。"""
    text = open(path, encoding="utf-8", errors="replace").read()
    return {"type": _field(text, "类型"), "loc": _field(text, "位置"),
            "sev": _field(text, "严重性"), "steps": _block(text, "Payload").splitlines(),
            "raw_request": _block(text, "raw_request"),
            "raw_response": _block(text, "raw_response"),
            "poc_time": _field(text, "时间"), "poc_env": _field(text, "环境")}


def final_prefix(review_dir, stem):
    """复核改名即结论变更：取最深一层复核文件名前缀（VULN/NOVULN/SUSPECTED）。"""
    cur = stem
    while True:
        cands = [f for f in os.listdir(review_dir)
                 if f.endswith(cur + ".md") and f[:-3] != cur]
        if not cands:
            return cur.split("-", 1)[0]
        cur = cands[0][:-3]


def _poc_missing(info):
    return [k for k, v in zip(POC_FIELDS, (info["raw_request"], info["raw_response"],
                                           info["poc_time"], info["poc_env"])) if not v]


def normalize(out_root, intent_id):
    fdir, rdir = os.path.join(out_root, "vuln_findings"), os.path.join(out_root, "vuln_reviews")
    facts, findings, assets = [], [], []
    for f in sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []:
        prefix, stem = f.split("-", 1)[0], f[:-3].split("-", 1)[1]
        final = final_prefix(rdir, f[:-3]) if os.path.isdir(rdir) else prefix
        if final == "NOVULN" or prefix == "NOVULN":
            facts.append({"kind": "info", "target": stem, "detail": "复核排除（NOVULN 终态）",
                          "confidence": 0.8})
            continue
        info = parse_finding(os.path.join(fdir, f))
        missing = _poc_missing(info)
        if missing:  # POC 四要素缺一=降级 fact 不成 finding（FD 报告卡规格 b0006f2）
            facts.append({"kind": "vuln-clue", "target": stem,
                          "detail": "POC 四要素缺 " + "/".join(missing)
                                    + "——降级 fact 不成 finding（FD 报告卡规格 b0006f2）",
                          "confidence": 0.6})
            continue
        findings.append({
            "title": "%s %s" % (info["type"] or "疑似漏洞", info["loc"] or stem),
            "confidence": CONF_MAP.get(final, "C3"),
            "impact": SEVERITY_MAP.get(info["sev"], "中"),
            "exploitation_status": "suspected", "auth_context": "",
            "reproducible_steps": info["steps"] + [info["raw_request"], info["raw_response"]],
            "evidence_refs": ["vuln_findings/" + f + "@" + info["poc_time"]],
            "location": info["loc"], "dedup_key_proposed": stem + "+src",
            "network_position": "same-host",
            "preconditions": ["目标源码可读（内部视角 L1）"],
            "expected_matcher": {}})
    sdir = os.path.join(out_root, "discovered_surfaces")
    for f in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        text = open(os.path.join(sdir, f), encoding="utf-8", errors="replace").read()
        src = re.search(r"\*\*来源\*\*：\s*(.+)", text)
        assets.append({"type": "source-code",
                       "value": (src.group(1).strip() if src else f), "meta": "surface-file=" + f})
        facts.append({"kind": "info", "target": f,
                      "detail": "攻击面条目：" + " ".join(text[:60].split()),
                      "confidence": 0.7})
    adir = os.path.join(out_root, "analyzed_surfaces")
    for f in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        text = open(os.path.join(adir, f), encoding="utf-8", errors="replace").read()
        facts.append({"kind": "info", "target": f,
                      "detail": "业务流分析：" + " ".join(text[:60].split()),
                      "confidence": 0.7})
    return {"intent_id": intent_id, "engine": "vuln-agent", "status": "done",
            "facts": facts, "findings": findings, "assets": assets,
            "edges": [], "creds": [], "operations_log": "operations.log"}


def _blocked(intent_id):
    return {"intent_id": intent_id, "engine": "vuln-agent", "status": "blocked",
            "facts": [], "findings": [], "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}


def _dump(sub, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sub, f, ensure_ascii=False, indent=1, sort_keys=True)


def parse_argv(argv):
    """--key=value 与 --key value 双形态归一（T5 裁决②同款 argv 契约）。"""
    args, i = {}, 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            if "=" in a:
                args.setdefault(a.partition("=")[0], a.partition("=")[2])
                i += 1
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args.setdefault(a, argv[i + 1])
                i += 2
            else:
                args.setdefault(a, "")
                i += 1
        else:
            i += 1
    return args


def main(argv):
    args = parse_argv(argv)
    for k in ("--intent-id", "--out-dir", "--source"):
        if not args.get(k):
            sys.stderr.write("用法: adapter.py --intent-id=I --out-dir=D --source=S [--run]\n")
            return 2
    out_root = os.path.join(args["--source"], ".vuln_agent_output")
    os.makedirs(args["--out-dir"], exist_ok=True)
    log = open(os.path.join(args["--out-dir"], "operations.log"), "w",
               encoding="utf-8", newline="\n")
    if "--run" in args:
        cmd = [RUN_PY.get(sys.platform, "python3"), "run.py"]
        r = subprocess.run(cmd, cwd=args["--source"], capture_output=True, text=True, timeout=3600)
        log.write("run: %s\nexit=%d\n%s\n%s\n" % (cmd, r.returncode, r.stdout, r.stderr))
        if r.returncode != 0:
            _dump(_blocked(args["--intent-id"]),
                  os.path.join(args["--out-dir"], "submission.json"))
            print("OK submission.json status=blocked reason=run-exit-%d" % r.returncode)
            return 0
    if not os.path.isdir(out_root):
        log.write("env: .vuln_agent_output 缺失\n")
        sys.stderr.write("ENV: .vuln_agent_output 缺失（--run 启动或提供既有输出）\n")
        return 2
    sub = normalize(out_root, args["--intent-id"])
    _dump(sub, os.path.join(args["--out-dir"], "submission.json"))
    log.write("normalize: findings=%d facts=%d assets=%d\n"
              % (len(sub["findings"]), len(sub["facts"]), len(sub["assets"])))
    print("OK submission.json findings=%d facts=%d assets=%d"
          % (len(sub["findings"]), len(sub["facts"]), len(sub["assets"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
