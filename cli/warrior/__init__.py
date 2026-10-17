# -*- coding: utf-8 -*-
"""战士运行时（W5）——自有战士循环进程包。

包引导：把 cli/ 前上 sys.path——与 tests/* 同款先例（cli 无 __init__.py，
ledger/tools 以 cli/ 为根导入；python3 -m cli.warrior 从仓根起跑即本包）。
"""
import os as _os
import sys as _sys

_CLI_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _CLI_DIR not in _sys.path:
    _sys.path.insert(0, _CLI_DIR)

WARRIOR_VERSION = "w5-warrior-1"
