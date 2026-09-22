#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli"))
from ledger import core
DENY = ["rm -rf /", "shutdown", "reboot", "mkfs", "curl evil.", "> /dev/sd"]
def main(argv):
    if len(argv) < 6 or argv[1] != "--goal-dir" or argv[3] != "--host" or argv[5] != "--":
        sys.stderr.write("usage" + chr(10))
        return 2
    gd, host, cmd = argv[2], argv[4], argv[6:]
    if host not in ("dsh", "opencode", "codex"):
        return 2
    joined = " ".join(cmd)
    for d in DENY:
        if d in joined:
            rows = core.Session(gd).rows("timeline.tsv")
            prev = rows[-1][6] if rows else "0" * 64
            wo = ["1970-01-01T00:00:00Z", "hook:" + host, "P3", "hook-block cmd=" + cmd[0], "", prev, "2"]
            h = core.row_hash(prev, wo)
            rows.append([wo[0], wo[1], wo[2], wo[3], wo[4], prev, h, "2"])
            core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)
            print("BLOCKED hook(%s) deny: %s" % (host, d))
            return 1
    print("PASS hook(%s)" % host)
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv))
