#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W2·CI 护栏（e7a6d5f1）——测试分片并行器（stdlib 零依赖律）。

用法:
  python scripts/shard_tests.py --list --shard=i/n   # 列出第 i 片模块名
  python scripts/shard_tests.py --run  --shard=i/n [--only=mod ...] [-v]
                                                     # 跑该片(透传 unittest rc)

分片律（tests/test_shard_tests.py 单测钉死）:
- 基元=tests/test*.py 模块(unittest 发现 pattern 同源)——单模块不跨片;
- 排序后轮转派片(index % n)——确定性: 同仓状态下片集恒等, 可重跑可比对;
- 片大小差 ≤1(计数均衡; 时长加权属后续批次, v1 不做);
- 空片 --run 直接 rc0(不进 unittest——无参 unittest 会回落全量发现, 反破坏分片);
- 非法片号(i<1 / i>n / n<1 / 非整数)=exit 2。

CI 接线(GitHub Actions): tests 作业 matrix 加 shard: ["1/4","2/4","3/4","4/4"],
每片 python scripts/shard_tests.py --run --shard=${{ matrix.shard }}——
四片并行墙钟 ≈ 全量/4 + 起动开销; 金样/evals 面不在此门(独立作业保持原样)。
"""
import argparse
import glob
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_modules():
    """全部测试模块名（排序恒定）。glob 基 = unittest 发现 pattern test*.py。"""
    files = sorted(glob.glob(os.path.join("tests", "test*.py")))
    return ["tests." + os.path.splitext(os.path.basename(f))[0] for f in files]


def parse_shard(spec):
    """'i/n' → (i, n)；非法 → None。"""
    try:
        i_s, n_s = spec.split("/", 1)
        i, n = int(i_s), int(n_s)
    except (ValueError, AttributeError):
        return None
    if n < 1 or i < 1 or i > n:
        return None
    return i, n


def shard_of(modules, i, n):
    """排序后轮转派片: 第 idx 模块属片 (idx % n) + 1。"""
    return [m for idx, m in enumerate(modules) if idx % n + 1 == i]


def main(argv=None):
    ap = argparse.ArgumentParser(description="确定性测试分片器")
    ap.add_argument("--list", action="store_true", help="列出该片模块名")
    ap.add_argument("--run", action="store_true", help="运行该片(透传 unittest rc)")
    ap.add_argument("--shard", default="1/1", help="片号 i/n（1 基）")
    ap.add_argument("--only", action="append", default=[],
                    help="只跑这些模块（自检/冒烟用，可多次）")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    sh = parse_shard(a.shard)
    if sh is None:
        sys.stderr.write("用法错误: --shard=i/n（1≤i≤n, n≥1）得: %s\n" % a.shard)
        return 2
    i, n = sh
    mods = test_modules()
    mine = shard_of(mods, i, n)
    if a.only:
        mine = [m for m in mods if m in set(a.only)] or list(a.only)
    if a.list:
        for m in mine:
            print(m)
        return 0
    if not mine:
        sys.stdout.write("[shard %s] empty shard——rc0 直通(不进 unittest)\n" % a.shard)
        return 0
    sys.stderr.write("[shard %s] %d modules\n" % (a.shard, len(mine)))
    cmd = [sys.executable, "-m", "unittest"] + (["-v"] if a.verbose else []) + mine
    rc = subprocess.call(cmd, cwd=REPO_ROOT)
    return rc


if __name__ == "__main__":
    sys.exit(main())
