# -*- coding: utf-8 -*-
"""T12 断点驱动子进程：argv=<goal-dir> <upto>；被父测试进程 subprocess.Popen 启动。"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)   # tests.* 可导入（与 unittest discover 同路径语义）
from tests.test_dryrun_p0p2 import dry_run_p0_p2, ledger, TS, STEPS

gd = sys.argv[1]
_, done = dry_run_p0_p2(gd, upto=int(sys.argv[2]))
# Ruling：checkpoint 步随断点驱动收尾（与层 A drive_with_checkpoint 同构）——
# 计划注释「驱动 12 步+checkpoint」与父测试「已写的 state 摘除」分支都要求
# state.md 存在；无此步则摘除分支恒死码、层 B 退化为纯缺省态恢复。
# Ruling：checkpoint --phase=驱动实际所处门（STEPS 按门有序，末步标签即当前门）。
# 计划字面的固定 P3 在截断账本上越位（verify-chain 跳门纪律正确拒收——真实
# 总控只会对当前门 checkpoint，不对未达门虚戳）。
phase = STEPS[done - 1][0] if done else "P0"
ledger(gd, "checkpoint", ["--session=s-k9", "--phase=" + phase,
                          "--note=k9", "--timestamp=" + TS])
sys.exit(0)   # 断点截断不算失败——保真度由父进程的恢复断言判定
