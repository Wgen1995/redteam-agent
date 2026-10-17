#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_lock —— cli/tools/tools.lock 重签工具（dev 侧；运行时只验不签）。

用法: python3 cli/tools/make_lock.py --key tests/fixtures/keys/test-signing-key.pem
默认用仓内测试钥重签全部注册卡（TEST-ONLY 锚，批次 4 先例）；生产钥离线仪式=
install/KEY-MANAGEMENT.md §3.4。改卡必重签（内容摘要入锚）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import cards as tool_cards  # noqa: E402
from tools import lock as tool_lock  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="make_lock")
    ap.add_argument("--key", default=os.path.join(
        REPO, "tests", "fixtures", "keys", "test-signing-key.pem"),
        help="签名私钥（缺省=仓内 TEST-ONLY 测试钥）")
    ap.add_argument("--out", default=tool_lock.DEFAULT_LOCK_PATH)
    a = ap.parse_args(argv)
    if not os.path.exists(a.key):
        sys.stderr.write("签名钥不存在: %s\n" % a.key)
        return 2
    entries = {}
    for c in tool_cards.all_cards():
        entries[c.name] = {"version": c.version,
                           "sha256": tool_lock.card_digest(c),
                           "sig": tool_lock.sign_card(c, a.key)}
    tool_lock.write_entries(a.out, entries)
    print("OK 重签 %d 卡 -> %s" % (len(entries), a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
