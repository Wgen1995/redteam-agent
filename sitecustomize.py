# -*- coding: utf-8 -*-
"""coverage 子进程计量钩（W2·CI 护栏⑤ e7a6d5f1）——只在 CI coverage 作业生效。

本仓测试面以 subprocess spawn 无扩展名 CLI（tanyin-guard/ledger/...）为主，
主进程 coverage 看不见子进程。标准解法（coverage 官方 subprocess 支持）：
coverage 作业带 COVERAGE_PROCESS_START 环境变量 + 本文件在 PYTHONPATH 上，
每个子解释器启动即挂计量（无环境变量=两行直通零开销，生产面零影响）。
"""
import os

if os.environ.get("COVERAGE_PROCESS_START"):
    try:
        import coverage
        coverage.process_startup()
    except Exception:
        pass   # 计量钩失败不拖垮被测进程
