# -*- coding: utf-8 -*-
"""规范化器：剥时间戳 + 行排序（字节级回归前提）"""
import re, sys
TS = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?")
out = [TS.sub("TS", l.rstrip()) for l in sys.stdin]
sys.stdout.write(chr(10).join(sorted(out)) + (chr(10) if out else ""))