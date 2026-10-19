# -*- coding: utf-8 -*-
"""engine_bridge(P0 T6)——读面写转发子进程(单写者纪律的执行面)。

铁律对齐(docs/superpowers/plans/2026-10-20-p0-command-deck.md):
- 写路径一律本桥子进程调 tanyin 命令链(tanyin-ledger …);读面 FastAPI
  进程零账本直写——say.py 只 subprocess 本脚本,不碰 battles 根。
- 引擎零改: 本桥只拼既有命令面参数,不改 cli/ 一行。
- P0 一律 --dry-run: 演练=算战号+拼 battle/new 链(add-goal+add-scope)
  回执,零目录零账本写入;真点火(fail-closed 拒,后续舰接线)。

CLI(仓库根):
  python3 server/readface/engine_bridge.py ignite \
      --target <目标> [--scope <匹配> ...] [--budget <预算句>] \
      [--note <说明>] --dry-run
stdout 末行=JSON 回执;rc: 0=演练成 / 2=用法或 fail-closed。
"""
import argparse
import json
import os
import re
import sys

# 仓根 cli/ 前上 sys.path(ledger_reader 同款先例),复用 battles 根单源。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_CLI_DIR = os.path.join(_REPO_ROOT, "cli")
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

from ledger.session_view import default_battles_dir   # noqa: E402

_LEDGER_CLI = os.path.join(_CLI_DIR, "tanyin-ledger")
_GEN_OF_NEW_BATTLE = "G-w1"     # 引擎 webui server.py 同位约定


def _emit(doc):
    print(json.dumps(doc, ensure_ascii=False))


def _next_battle_no(root):
    """根上最大 battle-N +1(引擎 webui _post_battle_new 同式)。"""
    try:
        nums = [int(m.group(1)) for e in os.listdir(root)
                for m in [re.match(r"^battle-(\d+)$", e)] if m]
    except OSError:
        nums = []
    return (max(nums) + 1) if nums else 1


def _ignite_chain(n, target, scopes, budget, note):
    """battle/new 链 argv 演练(引擎 webui 钮 1 同形;授权件字段=待补清单)。"""
    goal_dir = os.path.join(default_battles_dir(), "battle-%d" % n,
                            _GEN_OF_NEW_BATTLE)
    add_goal = [
        sys.executable, _LEDGER_CLI, "add-goal", "--goal-dir", goal_dir,
        "--target=" + target,
        "--objective=" + (note or "（说话开仗,未填说明）"),
        # 授权八问字段真点火时由授权件补齐(确认卡授权提示同源)——
        # dry-run 回执只报已知量,不编 sha/签名人。
        "--budget=<授权时定>",
        "--timestamp=<点火时>"]
    if budget:
        add_goal.append("--business-context=预算说明:" + budget)
    chain = [add_goal]
    for s in scopes:
        chain.append([
            sys.executable, _LEDGER_CLI, "add-scope", "--goal-dir", goal_dir,
            "--kind=include", "--matcher=" + s,
            "--note=说话开仗确认卡范围", "--timestamp=<点火时>"])
    return chain


def cmd_ignite(args):
    if not args.target.strip():
        _emit({"ok": False, "error": "target 必填(开仗目标不可为空)"})
        return 2
    if not args.dry_run:
        # fail-closed: 真点火 P0 未接线(授权件链/仲裁/runner 后续舰)。
        _emit({"ok": False, "error":
               "真点火未接线——P0 一律 --dry-run 演练;"
               "授权件+预算仲裁+runner spawn 见后续舰"})
        return 2
    root = default_battles_dir()
    n = _next_battle_no(root)
    chain = _ignite_chain(n, args.target.strip(),
                          [s.strip() for s in args.scope if s.strip()],
                          (args.budget or "").strip(), (args.note or "").strip())
    _emit({"ok": True, "dry_run": True, "battle": n,
           "battles_root": root,
           "goal_dir": os.path.join(root, "battle-%d" % n,
                                    _GEN_OF_NEW_BATTLE),
           "chain": [" ".join(step) for step in chain],
           "missing_for_real": [
               "auth-doc", "auth-sha256", "signer", "valid-from",
               "valid-until", "model-tier", "guard-tier"],
           "note": "P0 一律 dry-run: 链已演练(战号+参数),零目录零账本写入"})
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="engine_bridge")
    sub = p.add_subparsers(dest="cmd")
    ig = sub.add_parser("ignite", help="开仗(battle/new 链)")
    ig.add_argument("--target", default="", help="开仗目标(域名/IP/系统)")
    ig.add_argument("--scope", action="append", default=[],
                    help="范围匹配(可重复)")
    ig.add_argument("--budget", default="", help="预算说明句")
    ig.add_argument("--note", default="", help="补充说明")
    ig.add_argument("--dry-run", action="store_true",
                    help="演练不落账(P0 唯一允许模式)")
    args = p.parse_args(argv)
    if args.cmd == "ignite":
        return cmd_ignite(args)
    p.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
