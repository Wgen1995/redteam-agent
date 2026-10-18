#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evals/gt/gt_verify.py — GT 注册表校验器（数据件校验测的 CLI 面）。

职责（宪法#43 评测棘轮的测量地基件）：
  1. gt-index.tsv ↔ 战场文件 ↔ GT 行 三层一致性；
  2. source-gt 战场逐行实跑 verify_cmd（只读锚：grep/test 复合；黑名单词面硬拒）；
  3. --live 时对 ZhuLong 靶场仓只读实跑（锚根=靶场仓根；缺仓=退出码 2 ENV）。

口径：open=当前真发现；fixed-anchor=已修复伤疤的回归锚（锚消失=回退）；
neg=FP 诱饵负对（verify_cmd 锚定加固面在位——报告它=误报）。
退出码：0=全过；1=校验/锚失败；2=环境（锚根缺失）。
用法：
  python3 evals/gt/gt_verify.py [--root <锚根>] [--live] [--index <tsv>] [--json <out>]
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # redteam-agent 根
DEFAULT_INDEX = os.path.join(HERE, "gt-index.tsv")
ZL_REPO = os.path.expanduser(
    "~/Documents/AI For Security & Compliance/ai-assisted-security-verification-platform")

REQUIRED_FIELDS = ("id", "battlefield", "polarity", "status", "class", "cwe",
                   "severity", "title", "location", "finding", "verify_cmd",
                   "provenance", "entered_at")
POLARITIES = ("pos", "neg")
STATUSES = ("open", "fixed-anchor", "decoy")
SEVERITIES = ("Critical", "High", "Medium", "Low", "Info")
# 只读锚白名单：复合命令拆段后每段必须形如 grep/! grep/test（黑名单词面另硬拒）
_BLACKLIST = re.compile(r"\b(rm|mv|cp|touch|chmod|curl|wget|perl|find|xargs|tee|sh|bash)\b|>>?|\|")
_SEG = re.compile(r"^(?:!\s*)?(?:grep|test)\b")


def _segments(cmd):
    out = []
    for part in re.split(r"&&|\|\|", cmd):
        out.extend(s for s in part.split(";") if s.strip())
    return out


def check_verify_cmd(cmd):
    """verify_cmd 守卫：只读（grep/test 复合）。返回 (ok, why)。"""
    if not cmd or not cmd.strip():
        return False, "empty"
    body = re.sub(r"&&|\|\|", " ", cmd)   # 复合算子不算管道（先剥再查单管）
    if _BLACKLIST.search(body):
        return False, "blacklist-token"
    for seg in _segments(cmd):
        if not _SEG.match(seg.strip()):
            return False, "non-grep-segment:" + seg.strip()[:40]
    return True, ""


def load_index(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f.read().split("\n"):
            if not ln.strip() or ln.startswith("#"):
                continue
            cols = ln.split("\t")
            if len(cols) != 9:
                raise ValueError("index row must have 9 columns: " + ln[:80])
            rows.append(dict(zip(("battlefield", "kind", "gt_file", "true_findings",
                                  "decoys", "caliber", "status", "entered_at", "note"), cols)))
    return rows


def verify(index_path, root, want_json=None):
    failures, results = [], []
    idx = load_index(index_path)
    src_rows = [r for r in idx if r["kind"] == "source-gt"]
    if not src_rows:
        failures.append("index: no source-gt battlefield")
    for row in idx:
        target = row["gt_file"] if os.path.isabs(row["gt_file"]) else os.path.join(REPO, row["gt_file"])
        if not os.path.exists(target):
            failures.append("index->file missing: %s (%s)" % (row["battlefield"], target))
            continue
        if row["kind"] == "source-gt":
            with open(target, encoding="utf-8") as f:
                bf = json.load(f)
            pos = [r for r in bf["rows"] if r["polarity"] == "pos"]
            neg = [r for r in bf["rows"] if r["polarity"] == "neg"]
            if len(pos) != int(row["true_findings"]):
                failures.append("%s: true_findings %s != pos rows %d" % (row["battlefield"], row["true_findings"], len(pos)))
            if len(neg) != int(row["decoys"]):
                failures.append("%s: decoys %s != neg rows %d" % (row["battlefield"], row["decoys"], len(neg)))
            for r in bf["rows"]:
                miss = [k for k in REQUIRED_FIELDS if not r.get(k)]
                if miss:
                    failures.append("%s/%s: missing fields %s" % (row["battlefield"], r.get("id"), miss))
                if r.get("polarity") not in POLARITIES or r.get("status") not in STATUSES:
                    failures.append("%s/%s: bad polarity/status" % (row["battlefield"], r.get("id")))
                if r.get("severity") not in SEVERITIES:
                    failures.append("%s/%s: bad severity" % (row["battlefield"], r.get("id")))
                ok, why = check_verify_cmd(r.get("verify_cmd", ""))
                if not ok:
                    failures.append("%s/%s: verify_cmd unsafe (%s)" % (row["battlefield"], r.get("id"), why))
                    continue
                p = subprocess.run(["/bin/sh", "-c", r["verify_cmd"]], cwd=root,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                results.append({"id": r["id"], "polarity": r["polarity"], "status": r["status"],
                                "rc": p.returncode, "anchor_root": root})
                if p.returncode != 0:
                    failures.append("%s/%s: verify_cmd rc=%d" % (row["battlefield"], r["id"], p.returncode))
        elif row["kind"] == "replay-fixture":
            need = ("findings.tsv", "assets.tsv", "E-index.tsv", "timeline.tsv")
            for n in need:
                if not os.path.exists(os.path.join(target, n)):
                    failures.append("%s: fixture missing %s" % (row["battlefield"], n))
        elif row["kind"] == "session-gt":
            with open(target, encoding="utf-8") as f:
                gt = json.load(f)
            n = len(gt.get("planted", []))
            if n != int(row["true_findings"]):
                failures.append("%s: true_findings %s != planted %d" % (row["battlefield"], row["true_findings"], n))
    summary = {"format_version": 1, "index": index_path, "anchor_root": root,
               "rows_verified": len(results), "pass": len(results) - len([f for f in failures if "verify_cmd rc=" in f]),
               "fail": len(failures), "failures": failures, "results": results}
    if want_json:
        with open(want_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
    return summary


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="锚根（缺省=evals/gt/snapshots/zl-repo）")
    ap.add_argument("--live", action="store_true", help="对 ZhuLong 靶场仓只读实跑")
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--json", dest="out_json", default=None)
    a = ap.parse_args(argv)
    root = a.root or (ZL_REPO if a.live else os.path.join(HERE, "snapshots", "zl-repo"))
    if not os.path.isdir(root):
        print("ENV anchor-root missing: %s" % root)
        return 2
    s = verify(a.index, root, a.out_json)
    for f in s["failures"]:
        print("FAIL\t%s" % f)
    print("gt-verify rows=%d pass=%d fail=%d root=%s" % (s["rows_verified"], s["pass"], s["fail"], root))
    return 0 if s["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
