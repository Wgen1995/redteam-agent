#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""父代理检查点服务(8901)合成根一键重建(T14 治本: /tmp 重启即失,已三失)。

用法: python3 scripts/make_gl_review_home.py [--root /tmp/gl-review-home]
产物: <root>/battles/battle-1/G-r18(夹具整树副本)+runner(已点火未完跑)
      + <root>/channels.json(~/.tanyin 副件,600,say 真调用链)
重建后重起服务(命令见 docs/design/START-HERE.md):
  TANYIN_HOME=<root> READFACE_ALLOW_DEMO=1 nohup python3 -m uvicorn \
      server.readface.main:app --host 127.0.0.1 --port 8901 &
"""
import argparse
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(REPO, "tests", "fixtures", "G-r18")
SRC_CHANNELS = os.path.expanduser("~/.tanyin/channels.json")


def main():
    p = argparse.ArgumentParser(description="重建检查点合成根")
    p.add_argument("--root", default="/tmp/gl-review-home")
    a = p.parse_args()
    if os.path.exists(a.root):
        print("根已在: %s(不动;要重建先删)" % a.root)
        return 0
    b1 = os.path.join(a.root, "battles", "battle-1")
    os.makedirs(b1)
    shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
    with open(os.path.join(b1, "opencode-run.log.runner.tsv"), "w",
              encoding="utf-8") as f:
        f.write("2026-10-14T09:00:00Z\tBOOT\tup\n"
                "2026-10-14T09:00:05Z\tLAUNCH\topencode\n")
    if os.path.exists(SRC_CHANNELS):
        dst = os.path.join(a.root, "channels.json")
        shutil.copy2(SRC_CHANNELS, dst)
        os.chmod(dst, 0o600)
        ch = "channels.json 副件=true(say 真调用链在)"
    else:
        ch = "channels.json 副件=false(~/.tanyin 无此件,say 将无钥)"
    print("根已建: %s\n  battle-1=G-r18(执行中 runner)\n  %s" % (a.root, ch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
