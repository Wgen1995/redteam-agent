# -*- coding: utf-8 -*-
"""W5 知识环·蒸馏包（演进飞轮第 2 齿——战后复盘→知识蒸馏）。

python3 -m cli.knowledge distill <battle-dir>   规则蒸馏 v1 → 卡草案+人工确认位
python3 -m cli.knowledge confirm <draft.md>     人工确认后经 write_negative_card 入册
python3 -m cli.knowledge report <suite-dir>     逐战蒸馏报告聚合

包引导：把 cli/ 前上 sys.path（cli 无 __init__.py，ledger/tools 以 cli/ 为根
导入——cli.warrior 同款先例）。
"""
import os as _os
import sys as _sys

_CLI_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _CLI_DIR not in _sys.path:
    _sys.path.insert(0, _CLI_DIR)

DISTILL_VERSION = "distill-rules-v1"
