#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§9.4 双知识库抽查 eval（批次5 T18；出口验收①②判定命令，CI 可重放）。

四判据：①字段完整=tanyin-knowledge lint 全 PASS；②指纹可检索=先例页逐页自反
match 命中（含 [expired]/[stale] 标注形态——「可检索」语义）+实体页 neighbors
非空；③无跨客户残留=全页真域名/IP 形态扫描（CLIENT-NN 与白名单 example.com/
test/localhost/占位符外零容忍——DOMAIN_RE/IP_RE 与 lint 同源单源复用）；④CVE
核验标记齐全（限 --origin=external：cve_refs 非空页全核验+verified_at 无未来
时间戳）。exit 0=全过 / 1=FAIL 清单 / 2=环境。

抽查范围口径（G-35）：以在库页为准——素材降级登记（SOURCES 待补行）不产出蒸馏
页，不阻塞抽查；④只消费在库页自带的 cve_refs/cve_verified 标记。

种子库只读：探针一律在 --knowledge-dir 的整库临时副本上执行（R7 只读纪律+R8
lint 落审计行——就地直跑会写热仓库种子库，T18 前置隔离修复同因）；副本只读拷贝
上判定语义与原库等价。一切时间显式传入（--today，G-23/G-34 禁墙钟同律）。
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
KN = os.path.join(HERE, "..", "cli", "tanyin-knowledge")
from ledger import knowledge as kn_mod  # DOMAIN_RE/IP_RE/LINT_ZONES 与 lint 同源单源

# ③ 白名单（计划口径：example.com/test/localhost/占位符外零容忍；RFC 2606 保留域
# example.*/*.test 与 localhost 系均为文档正当形态）
WHITELIST_EXACT = ("example.com", "example.org", "example.net", "localhost", "test")


def kn(kd, *args):
    return subprocess.run([sys.executable, KN] + list(args) + ["--knowledge-dir", kd],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def read_page(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return {}, text
    head, _, body = text[3:].partition("---")
    fm = {}
    for ln in head.splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            fm[k.strip()] = v.strip()
    return fm, text


def iter_pages(kd):
    for zone in kn_mod.LINT_ZONES:
        d = os.path.join(kd, zone)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md"):
                yield os.path.join(d, fn)


def domain_whitelisted(name):
    n = name.lower()
    return (n in WHITELIST_EXACT or n.endswith(".test")
            or n.endswith(".localhost") or n.endswith(".example.com"))


def main():
    ap = argparse.ArgumentParser(description="§9.4 双知识库抽查（四判据）")
    ap.add_argument("--knowledge-dir", required=True)
    ap.add_argument("--origin", choices=("cnpen", "external"), default=None)
    ap.add_argument("--today", required=True)
    a = ap.parse_args()
    try:
        datetime.date.fromisoformat(a.today)
    except ValueError:
        sys.stderr.write("环境问题: --today 须 ISO 日期: %r\n" % a.today)
        return 2
    if not os.path.isdir(a.knowledge_dir):
        sys.stderr.write("环境问题: knowledge 目录不存在: %s\n" % a.knowledge_dir)
        return 2
    fails = []
    with tempfile.TemporaryDirectory() as td:
        kd = os.path.join(td, "knowledge")
        shutil.copytree(a.knowledge_dir, kd)
        r = kn(kd, "lint", "--today=" + a.today)                 # ① 字段完整
        if r.returncode == 2:
            sys.stderr.write("环境问题: lint exit 2\n" + r.stderr)
            return 2
        if r.returncode != 0:
            fails.append("字段完整: lint FAIL\n    " + r.stdout.strip().replace("\n", "\n    "))
        re_ = kn(kd, "export")                                    # 实体 neighbors 前置（副本上重建）
        if re_.returncode != 0:
            fails.append("导出: export FAIL\n    " + re_.stderr.strip())
        for p in iter_pages(kd):                                  # ② 指纹自反可检索
            fm, _raw = read_page(p)
            if fm.get("kind") == "precedent" and fm.get("client") and fm.get("scope_asset"):
                asset = str(fm["scope_asset"]).split(";")[0]
                m = kn(kd, "match", "--client=" + str(fm["client"]),
                       "--asset=" + asset, "--today=" + a.today)
                if str(fm.get("id", "")) not in m.stdout:
                    fails.append("指纹可检索: %s 自反未命中" % fm.get("id", p))
            elif fm.get("kind") == "entity" and fm.get("entity"):
                n = kn(kd, "neighbors", "--entity=" + str(fm["entity"]))
                tail = [ln for ln in n.stdout.strip().splitlines()
                        if ln.startswith("neighbors=")]
                if not tail or tail[-1].strip() == "neighbors=0":
                    fails.append("指纹可检索: 实体页 %s neighbors 空" % fm.get("id", p))
        for p in iter_pages(kd):                                  # ③ 无跨客户残留
            rel = os.path.relpath(p, kd)
            with open(p, encoding="utf-8") as f:
                for i, ln in enumerate(f, 1):
                    dm = kn_mod.DOMAIN_RE.search(ln)
                    if dm and not domain_whitelisted(dm.group(0)):
                        fails.append("无跨客户残留: %s:%d 真域名形态 %s"
                                     % (rel, i, dm.group(0)))
                    im = kn_mod.IP_RE.search(ln)
                    if im:
                        fails.append("无跨客户残留: %s:%d IP 形态 %s"
                                     % (rel, i, im.group(0)))
        if a.origin == "external":                                # ④ CVE 核验标记齐全
            for p in iter_pages(kd):
                fm, raw = read_page(p)
                refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c.strip()]
                if not refs:
                    continue
                verified = set(re.findall(r"cve\s*:\s*(CVE-[\d-]+)", raw))
                missing = [c for c in refs if c not in verified]
                future = [d for d in re.findall(r"verified_at\s*:\s*(\d{4}-\d{2}-\d{2})", raw)
                          if d > a.today]
                if missing or future:
                    fails.append("CVE 核验标记: %s%s%s" % (
                        os.path.relpath(p, kd),
                        (" 未核验:" + ",".join(missing)) if missing else "",
                        (" 未来时间戳:" + ",".join(future)) if future else ""))
    if fails:
        print("spotcheck FAIL %d 项：" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("spotcheck PASS（四判据全过）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
