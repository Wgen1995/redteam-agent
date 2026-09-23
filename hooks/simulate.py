#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tier 2 宿主 hook 模拟器（批次 2 T7）——dsh/opencode/codex 三模板同源语义：
deny-list 比对 + scope 解析；阻断=非零退出码 + timeline hook-block 事件；fail-closed。
SECW-3：补齐此前缺席的 scope 界外解析（SECW-1 盘点差距 1），与 tanyin-guard
共用 cli/ledger/enforce.py 单源；真宿主挂载=批次 6。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli"))
from ledger import core
from ledger import enforce
from ledger.schemas import TABLES


def hook_block(gd, host, event):
    rows = core.Session(gd).rows("timeline.tsv")
    hi = TABLES["timeline.tsv"].index("hash")
    prev = rows[-1][hi] if rows else core.GENESIS
    wo = ["1970-01-01T00:00:00Z", "hook:" + host, "P3", event, "", prev, "2"]
    h = core.row_hash(prev, wo)
    rows.append([wo[0], wo[1], wo[2], wo[3], wo[4], prev, h, "2"])
    core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)


def main(argv):
    if len(argv) < 6 or argv[1] != "--goal-dir" or argv[3] != "--host" or argv[5] != "--":
        sys.stderr.write("usage" + chr(10))
        return 2
    gd, host, cmd = argv[2], argv[4], argv[6:]
    if host not in ("dsh", "opencode", "codex"):
        return 2
    joined = " ".join(cmd)
    d = enforce.deny_hit(joined)
    if d:
        hook_block(gd, host, "hook-block cmd=" + cmd[0] + " deny=" + d)
        print("BLOCKED hook(%s) deny: %s" % (host, d))
        return 1
    bad = enforce.out_of_scope_hosts(cmd, enforce.load_scope(core.Session(gd)))
    if bad:
        hook_block(gd, host, "hook-block out-of-scope host=" + bad[0])
        print("BLOCKED hook(%s) out-of-scope: %s" % (host, bad[0]))
        return 1
    print("PASS hook(%s)" % host)
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv))
