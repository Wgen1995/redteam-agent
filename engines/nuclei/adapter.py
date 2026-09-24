#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nuclei adopt 适配器（批4 T10，契约 10/08）——JSONL→统一提交 schema。

启动先验签（验签先于归一化）：tools.lock 两键（nuclei/nuclei-templates）ECDSA 验签
（release.pub）+templates.lock 逐文件 sha256——不过=blocked 提交（环境受阻语义，
exit 0；log 落缘由）。--jsonl-file=canned 归一化（离线/测试）；--run=nuclei 经
tanyin-guard exec 执行通道（铁律 7：对外请求例外之执法通道）——可执行缺失=blocked
（运行时绝不自动安装，契约 10 §4）。severity→impact 映射；模板 id 进
dedup_key_proposed；matcher-name→expected_matcher word（契约 06 R1 子集）。"""
import hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import supply_chain  # noqa: E402

SEV2IMPACT = {"critical": "高", "high": "高", "medium": "中", "low": "低", "info": "低"}
USAGE = "用法: adapter.py --intent-id=I --out-dir=D [--lock=L] " \
        " (--jsonl-file=F | --goal-dir=G --target=URL --run)\n"


def verify(lock_path):
    """返回 (ok, reason)；False→适配器落 blocked 提交（环境受阻语义）。
    lock 解析失败（非五字段行等 ValueError）同=失败对非崩溃——「不过=blocked」
    exit 0 契约语义（批次 4 评审收尾 fail-closed 形式统一）。"""
    try:
        lock = supply_chain.load_lock(lock_path)
    except ValueError as e:
        return False, "tools.lock 解析失败（fail-closed=blocked）: %s" % e
    pub = os.path.join(HERE, "release.pub")
    for k in ("nuclei", "nuclei-templates"):
        if k not in lock:
            return False, "tools.lock 缺键 " + k
        ok, reason = supply_chain.verify_entry(lock[k], pub)
        if not ok:
            return False, "%s 验签失败: %s" % (k, reason)
    commit = lock["nuclei-templates"]["commit"]
    for ln in open(os.path.join(HERE, "templates.lock"), encoding="utf-8").read().splitlines()[1:]:
        path, _, sha = ln.rstrip("\n").rpartition("\t")
        if not path:
            continue
        fp = os.path.join(HERE, path)
        if not os.path.isfile(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != sha:
            return False, "模板快照 sha256 不符: " + path
    return True, commit


def normalize(jsonl_path, intent_id):
    findings = []
    for ln in open(jsonl_path, encoding="utf-8", errors="replace"):
        if not ln.strip():
            continue
        j = json.loads(ln)
        info = j.get("info", {})
        matcher = j.get("matcher-name") or ""
        findings.append({
            "title": info.get("name", j.get("template-id", "?")),
            "confidence": "C3",
            "impact": SEV2IMPACT.get(str(info.get("severity", "unknown")).lower(), "中"),
            "exploitation_status": "suspected", "auth_context": "",
            "reproducible_steps": ["nuclei -t %s -u %s" % (j.get("template-path", ""), j.get("host", ""))],
            "evidence_refs": [], "location": j.get("matched-at", j.get("host", "")),
            "dedup_key_proposed": j.get("template-id", "") + "+nuclei",
            "network_position": "internet",
            "preconditions": ["目标可达（internet 视角）"],
            "expected_matcher": ({"matchers": [{"type": "word", "words": [matcher]}]}
                                 if matcher else {})})
    return {"intent_id": intent_id, "engine": "nuclei", "status": "done",
            "facts": [], "findings": findings, "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}


def _blocked(intent_id):
    return {"intent_id": intent_id, "engine": "nuclei", "status": "blocked",
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
    for k in ("--intent-id", "--out-dir"):
        if not args.get(k):
            sys.stderr.write(USAGE)
            return 2
    jsonl = args.get("--jsonl-file", "")
    run_mode = "--run" in args
    if not jsonl and not run_mode:
        sys.stderr.write(USAGE)
        return 2
    if run_mode and not (args.get("--goal-dir") and args.get("--target")):
        sys.stderr.write(USAGE)
        return 2
    os.makedirs(args["--out-dir"], exist_ok=True)
    log = open(os.path.join(args["--out-dir"], "operations.log"), "w",
               encoding="utf-8", newline="\n")
    ok, reason = verify(args.get("--lock", "") or os.path.join(ROOT, "tools.lock"))
    if not ok:
        _dump(_blocked(args["--intent-id"]),
              os.path.join(args["--out-dir"], "submission.json"))
        log.write("verify: FAIL %s\n" % reason)
        print("OK submission.json status=blocked reason=%s" % " ".join(reason.split())[:100])
        return 0
    log.write("verify: ok templates_commit=%s\n" % reason)
    if jsonl:
        sub = normalize(jsonl, args["--intent-id"])
        _dump(sub, os.path.join(args["--out-dir"], "submission.json"))
        log.write("normalize: findings=%d\n" % len(sub["findings"]))
        print("OK submission.json status=done findings=%d" % len(sub["findings"]))
        return 0
    # --run：nuclei 经 tanyin-guard exec 执行通道（绝不自动安装）
    if shutil.which("nuclei") is None:
        _dump(_blocked(args["--intent-id"]),
              os.path.join(args["--out-dir"], "submission.json"))
        log.write("env: nuclei 可执行缺失（运行时绝不自动安装——契约 10 §4）\n")
        print("OK submission.json status=blocked reason=nuclei-missing")
        return 0
    guard = os.path.join(ROOT, "cli", "tanyin-guard")
    cmd = [sys.executable, guard, "exec", "--goal-dir", args["--goal-dir"], "--",
           "nuclei", "-jsonl", "-t", os.path.join(HERE, "templates"),
           "-u", args["--target"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                       encoding="utf-8", errors="replace")
    outl = os.path.join(args["--out-dir"], "nuclei-output.jsonl")
    with open(outl, "w", encoding="utf-8", newline="\n") as f:
        f.write(r.stdout)
    log.write("run: %s\nexit=%d\n" % (" ".join(cmd), r.returncode))
    if r.returncode != 0:
        _dump(_blocked(args["--intent-id"]),
              os.path.join(args["--out-dir"], "submission.json"))
        print("OK submission.json status=blocked reason=guard-exit-%d" % r.returncode)
        return 0
    sub = normalize(outl, args["--intent-id"])
    _dump(sub, os.path.join(args["--out-dir"], "submission.json"))
    log.write("normalize: findings=%d\n" % len(sub["findings"]))
    print("OK submission.json status=done findings=%d" % len(sub["findings"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
