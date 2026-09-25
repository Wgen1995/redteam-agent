#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向验证零命中 eval（批次5 T18；出口验收③判定命令，CI 可重放）——脏/净双向
断言防假绿。

在 --goal-dir 的整库临时副本上写两份草稿各跑一次 tanyin-redact --reverse-verify：
脏草稿（内嵌交战区 assets.value 首个真值）必须 exit 1（dirty=detected）；净草稿
（CLIENT-NN/占位符化）必须 exit 0（clean=zero-hits）。任一向不成立=exit 1（防
「永远 FAIL/永远 PASS」两种坏实现）。副本执行=仓内夹具零写热（R-RC-2「仓内夹具
禁就地跑门」先例同型——reverse-verify 只读，但草稿载体必须落盘）。exit 0=双向
断言成立 / 1=断言破 / 2=环境。
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REDACT = os.path.join(HERE, "..", "cli", "tanyin-redact")


def rv(goal, target_rel):
    return subprocess.run([sys.executable, REDACT, "--goal-dir", goal,
                           "--reverse-verify", "--target=" + target_rel],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def first_asset_value(goal):
    """assets.tsv 首个非空 value（脏样本真值源——eval 自取，不硬编码夹具内容）。
    表头行有无两态都收：无表头（G-g1 夹具形态）按 assets schema 列序 id/type/value
    取第 3 列（core.TABLES 单源列序）。"""
    p = os.path.join(goal, "assets.tsv")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    if not rows:
        return None
    if "value" in rows[0]:
        ci = rows[0].index("value")
        body = rows[1:]
    else:
        ci = 2
        body = rows
    for cells in body:
        if len(cells) > ci and cells[ci].strip():
            return cells[ci].strip()
    return None


def main():
    ap = argparse.ArgumentParser(description="反向验证零命中 eval（脏/净双向断言）")
    ap.add_argument("--goal-dir", required=True)
    a = ap.parse_args()
    if not os.path.isdir(a.goal_dir):
        sys.stderr.write("环境问题: goal 目录不存在: %s\n" % a.goal_dir)
        return 2
    value = first_asset_value(a.goal_dir)
    if not value:
        sys.stderr.write("环境问题: assets.tsv 无 value 行可作脏样本\n")
        return 2
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, "goal")
        shutil.copytree(a.goal_dir, g)
        os.makedirs(os.path.join(g, "report"), exist_ok=True)
        dirty_rel = os.path.join("report", "eval-dirty-draft.md")
        clean_rel = os.path.join("report", "eval-clean-draft.md")
        with open(os.path.join(g, dirty_rel), "w", encoding="utf-8", newline="\n") as f:
            f.write("# 评估草稿（脏样本）\n\n目标 %s 的边界确认记录。\n" % value)
        with open(os.path.join(g, clean_rel), "w", encoding="utf-8", newline="\n") as f:
            f.write("# 评估草稿（净样本）\n\n目标 CLIENT-NN（占位符化）的边界确认记录。\n")
        rd = rv(g, dirty_rel)
        rc_ = rv(g, clean_rel)
    ok = True
    if rd.returncode == 1:
        print("dirty=detected")
    else:
        ok = False
        print("dirty=NOT-detected（脏草稿未被拦截 rc=%d）%s"
              % (rd.returncode, (rd.stdout + rd.stderr).strip()))
    if rc_.returncode == 0:
        print("clean=zero-hits")
    else:
        ok = False
        print("clean=HITS（净草稿误报 rc=%d）%s"
              % (rc_.returncode, (rc_.stdout + rc_.stderr).strip()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
