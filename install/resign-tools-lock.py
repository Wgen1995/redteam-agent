#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install/resign-tools-lock.py · tools.lock 整锁重签（G-22；批次 6 T9）。

用法：python3 install/resign-tools-lock.py --lock tools.lock --key <私钥.pem> [--out <路径>]

- 逐键 sign_entry(canonical_digest)（cli/ledger/supply_chain.py 单源，签名覆盖=行前四
  字段规范串「键\t版本\tsha256\t」的 sha256 digest）→ 原子写回（临时文件+os.replace）；
- 非交互纪律：不读 stdin；生产钥生成/保管/重签仪式=KEY-MANAGEMENT.md §3（离线介质机
  人工执行）。--allow-online 缺省时打印提示行后照常执行——提示非拦截：CI 测试链用
  TEST-ONLY 夹具钥（tests/fixtures/keys/，与生产 release.pub 无信任关系）在仓内可重签；
  生产钥永不进仓。
- 注释行/format_version 行原样保留；非五字段行原样保留（load_lock 侧 fail-closed 兜底）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli"))
from ledger import supply_chain  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser(prog="resign-tools-lock")
    ap.add_argument("--lock", required=True, help="tools.lock 路径")
    ap.add_argument("--key", required=True, help="EC 私钥 PEM（生产钥=离线机人工仪式）")
    ap.add_argument("--out", default=None, help="输出路径（缺省=原地原子写回）")
    ap.add_argument("--allow-online", action="store_true",
                    help="在线机确认行（提示非拦截；生产钥仪式仍须离线介质机）")
    a = ap.parse_args(argv)
    if not a.allow_online:
        print("提示：生产钥重签须离线介质机执行（KEY-MANAGEMENT.md §3）；"
              "本提示非拦截——测试/演练链用 TEST-ONLY 夹具钥照常执行。")
    if not os.path.exists(a.key):
        print("私钥缺: %s" % a.key)
        return 2
    with open(a.lock, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, n = [], 0
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) == 5 and not ln.startswith("#"):
            e = dict(zip(supply_chain.FIELDS, parts))
            e["sig"] = supply_chain.sign_entry(e, a.key)
            out.append("\t".join(e[f] for f in supply_chain.FIELDS))
            n += 1
        else:
            out.append(ln)
    dst = a.out or a.lock
    tmp = dst + ".resign-tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, dst)
    print("resign ok: %d 键 → %s" % (n, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
