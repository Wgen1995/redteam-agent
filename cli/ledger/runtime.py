# -*- coding: utf-8 -*-
"""runtime · v0.7 CLI 脚手架单源（抽取试点）。

每个 cli/tanyin-* 入口重复的三件事收拢于此：
sys.path 注入（可 import ledger.*）/ UTF-8 stdio（Windows 控制台防 UnicodeEncodeError）/
返回 cli 目录（调用者按需拼路径）。
迁移律：一次迁冷路径脚本（试点），战斗热路径（runner/battle/ledger 核心）战后批走。"""
import os
import sys

from .core import ensure_utf8_stdio


def bootstrap(caller_file):
    """CLI 入口脚手架。caller_file=__file__；返回 cli 目录 Path(str)。

    幂等：重复 bootstrap 不重复插 path。"""
    d = os.path.dirname(os.path.abspath(caller_file))
    if d not in sys.path:
        sys.path.insert(0, d)
    ensure_utf8_stdio()
    return d
