# -*- coding: utf-8 -*-
"""规范化器：剥时间戳 + 行排序（字节级回归前提）"""
import re, sys

for _s in (sys.stdin, sys.stdout):  # Windows 管道默认 GBK：统一 UTF-8（老 python 无 reconfigure 则跳过）
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

TS = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
out = [TS.sub("TS", l.rstrip()) for l in sys.stdin]
sys.stdout.write(chr(10).join(sorted(out)) + (chr(10) if out else ""))
