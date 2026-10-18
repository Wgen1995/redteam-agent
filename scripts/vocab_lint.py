#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vocab_lint——人话词表过滤(宪法62律的机检面;驾驶舱三层验收之一)。

扫描 webui 可见文本(剥 <script>/<style> 后的文本节点 + placeholder/title/aria-label),
命中黑话词表即报——屏上说人话,代码标识符/API字段名不受限。
用法: python3 scripts/vocab_lint.py [--dir cli/webui/static] [--quiet]
退出码: 0=干净 1=有黑话 2=环境错。
"""
import argparse, re, sys
from pathlib import Path

# 黑话→人话(屏上禁黑话,改用右列)
BANNED = {
    "finding": "漏洞", "findings": "漏洞", "intent": "任务", "intents": "任务",
    "warrior": "士兵", "credential": "钥匙", "credentials": "钥匙",
    "asset": "目标", "assets": "目标", "evidence card": "证据", "EV卡": "证据",
    "ledger": "战账", "distill": "战果提炼", "submatrix": "子矩阵页",
}
# 白名单: 技术专名/设置页允许
ALLOWED = {"SARIF", "API", "URL", "HTTP", "token", "Token", "CLI", "JSON", "TSV"}
TAG_STRIP = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
ATTR = re.compile(r'(?:placeholder|title|aria-label)\s*=\s*["\']([^"\']*)["\']')

def visible_text(html: str) -> str:
    html = TAG_STRIP.sub(" ", html)
    parts = [TAGS.sub(" ", html)]
    parts += ATTR.findall(html)
    return " ".join(parts)

def lint_file(p: Path):
    hits = []
    text = visible_text(p.read_text(encoding="utf-8", errors="ignore"))
    low = text.lower()
    for bad, good in BANNED.items():
        for m in re.finditer(r"\b" + re.escape(bad) + r"\b", low, re.I):
            frag = text[max(0, m.start()-25):m.end()+25].strip()
            if any(a.lower() in frag.lower() for a in ALLOWED if len(a) > 3):
                continue
            hits.append((bad, good, frag[:60]))
            break  # 每词每文件报一次
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="cli/webui/static")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    root = Path(a.dir)
    if not root.is_dir():
        print(f"rc2 目录不存在: {a.dir}"); return 2
    total = 0
    for p in sorted(root.rglob("*.html")):
        for bad, good, frag in lint_file(p):
            total += 1
            if not a.quiet:
                print(f"黑话 {bad!r}→应用『{good}』 @ {p.name}: …{frag}…")
    if not a.quiet:
        print(f"rc{1 if total else 0} 扫描完成: {total} 处黑话" if total else "rc0 词表干净")
    return 1 if total else 0

if __name__ == "__main__":
    sys.exit(main())
