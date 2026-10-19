# -*- coding: utf-8 -*-
"""T13 E2E 合成根制造器——tests/readface 造法单源复用,零第二份。

造法(=T12 test_findings._Syn + T10 test_say 微型在跑仗,同律):
- battle-1: G-r18 夹具整树副本 + BOOT/LAUNCH 未完跑 runner(log)→账本可读
  (76 发现/6 兵/全量 timeline,发现页统计+灰卡+详情抽屉数据源);
- battle-2: 微型在跑仗——接链 timeline(add-goal + warrior-start w1 +
  warrior-heartbeat w2,引擎 chained_row 真链形)+ goals.tsv + FD-s-9
  无证据发现(422 路已有单测罩,E2E 不点它)+ 未完跑 runner→执行中
  (在跑仗条/插话/全停的对象,dry-run 战号=根上最大 2→3);
- channels.json: ~/.tanyin/channels.json 副件(在场才拷;不在场=
  LLM 链必败,say 步由套件如实标 SKIP)。

根是纯合成(TANYIN_HOME 指向它),每次调用新根,完清由调用方负责;
不碰 /tmp/gl-review-home 等任何既有家。

用法: python3 make_root.py --root DIR
输出: 单行 JSON {"root", "battles", "channels_copied"}(套件解析)。
"""
import argparse
import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "cli"))

from ledger import core as ledger_core          # noqa: E402
from ledger import timeline as ledger_timeline  # noqa: E402
from ledger.schemas import TABLES               # noqa: E402

FIXTURE = os.path.join(REPO_ROOT, "tests", "fixtures", "G-r18")

# 微型在跑仗 timeline(=tests/readface/test_say._TL_RUNNING 同三条,仗名改本根):
# 立卡 + w1 在编(start)+ w2 活跃(heartbeat)→插话扇出 w1,w2,全停同。
_TL_RUNNING = [
    ("2026-10-20T09:00:00Z", "op", "P0", "add-goal G-1 target=10.2.0.7", ""),
    ("2026-10-20T09:00:05Z", "runner", "P3",
     "warrior-start battle=battle-2 warrior=w1 pid=101 model=strong", ""),
    ("2026-10-20T09:00:06Z", "warrior:w2", "P3",
     "warrior-heartbeat warrior=w2 intent=INT-2", ""),
]

# FD-s-9: 无绑定证据卡的发现(=T12 造法;灰卡区可见,reverify 会 422,
# E2E 点的是 FD-r18-0076,此行只为统计口径与 T12 单测对齐)。
_FD_NO_EV = {"id": "FD-s-9", "title": "no ev", "confidence": "C2",
             "affected_asset_id": "AST-s-1", "status": "active"}


def _chain(spec):
    """[(ts,actor,phase,event,revert)...] → 引擎真实接链 8 列行(单源复用)。"""
    rows = []
    for ts, actor, phase, event, revert in spec:
        row, _prev = ledger_timeline.chained_row(rows, ts, actor, phase,
                                                 event, revert)
        rows.append(row)
    return rows


def _mk_goal(gd, tl_spec, tables=None):
    """微型 goal: 接链 timeline + 若干净表(write_tsv 落盘,缺列补空)。"""
    os.makedirs(gd, exist_ok=True)
    ledger_core.write_tsv(os.path.join(gd, "timeline.tsv"), _chain(tl_spec))
    for tname, dict_rows in (tables or {}).items():
        cols = TABLES[tname]
        ledger_core.write_tsv(
            os.path.join(gd, tname),
            [[d.get(c, "") for c in cols] for d in dict_rows])


def _mk_runner(battle_dir):
    """runner 生命周期 log: BOOT/LAUNCH 无 DONE=已点火未完跑(执行中口径)。"""
    with open(os.path.join(battle_dir, "opencode-run.log.runner.tsv"),
              "w", encoding="utf-8") as f:
        f.write("2026-10-20T09:00:00Z\tBOOT\tup\n"
                "2026-10-20T09:00:05Z\tLAUNCH\topencode\n")


def main():
    p = argparse.ArgumentParser(prog="make_root")
    p.add_argument("--root", required=True, help="合成根目录(须不存在或空)")
    a = p.parse_args()

    root = os.path.abspath(a.root)
    if os.path.exists(root) and os.listdir(root):
        print(json.dumps({"error": "root 非空: %s" % root}))
        return 2

    # battle-1: G-r18 副本(夹具整树)+ 未完跑 runner
    b1 = os.path.join(root, "battles", "battle-1")
    os.makedirs(b1)
    shutil.copytree(FIXTURE, os.path.join(b1, "G-r18"))
    _mk_runner(b1)

    # battle-2: 微型在跑仗(接链 timeline + goals + 无证据发现 + runner)
    b2 = os.path.join(root, "battles", "battle-2")
    _mk_goal(os.path.join(b2, "G-1"), _TL_RUNNING,
             {"goals.tsv": [{"id": "G-1", "target": "10.2.0.7"}],
              "findings.tsv": [_FD_NO_EV]})
    _mk_runner(b2)

    # channels.json 副件(在场才拷;say 意图解析读 $TANYIN_HOME/channels.json)
    src = os.path.join(os.path.expanduser("~/.tanyin"), "channels.json")
    copied = False
    if os.path.isfile(src):
        shutil.copyfile(src, os.path.join(root, "channels.json"))
        copied = True

    print(json.dumps({"root": root,
                      "battles": ["battle-1", "battle-2"],
                      "channels_copied": copied}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
