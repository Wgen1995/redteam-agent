# -*- coding: utf-8 -*-
"""战士入口（W5 战士 MVP）——python3 -m cli.warrior。

用法：
  python3 -m cli.warrior --goal-dir D --battle-name X --max-intents N \
      [--channels PATH.json] [--dry-run] [--warrior-id W-1]
      [--lease-min 30] [--token-cap N] [--time-window-min N]
      [--heartbeat-min 5] [--stall-min 15] [--ctx-tokens 24000]
      [--max-turns 6] [--respawn-max 2] [--skill PATH]
      [--tools-state PATH] [--max-parallel-tools 16]

--channels=有序通道链 JSON（[{"name","model","base_url","api_key"}…]，
llmpool 按序健康选道）；--dry-run=只组上下文打印，不领/不写/不调模型。
停滞重生：status=stalled → 重建新循环（新脑，R1 全新上下文）至
--respawn-max 耗尽（退出码 3）；停状态经 timeline warrior-start/stop 行
全程留痕。退出码：0 优雅停 / 2 用法环境 / 3 重生耗尽 / 1 异常。
"""
import json
import os
import sys

if __package__ in (None, ""):                       # 直跑兼容
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))

from warrior import loop as loop_mod            # noqa: E402

USAGE = ("用法: python3 -m cli.warrior --goal-dir D --battle-name X "
         "--max-intents N [--channels PATH.json] [--dry-run] "
         "[--warrior-id W-1] [--lease-min 30] [--token-cap N] "
         "[--time-window-min N] [--heartbeat-min 5] [--stall-min 15] "
         "[--ctx-tokens 24000] [--max-turns 6] [--respawn-max 2] "
         "[--skill PATH] [--tools-state PATH] [--max-parallel-tools 16]")

_KNOWN = {
    "--goal-dir": "goal_dir", "--battle-name": "battle_name",
    "--max-intents": "max_intents", "--channels": "channels_path",
    "--warrior-id": "warrior_id", "--lease-min": "lease_min",
    "--token-cap": "token_cap", "--time-window-min": "time_window_min",
    "--heartbeat-min": "heartbeat_min", "--stall-min": "stall_min",
    "--ctx-tokens": "ctx_tokens", "--max-turns": "max_turns",
    "--respawn-max": "respawn_max", "--skill": "skill_path",
    "--tools-state": "tools_state",
    "--max-parallel-tools": "max_parallel_tools",
}


def parse_args(argv):
    out = {"warrior_id": "warrior:W-1", "lease_min": 30,
           "token_cap": 100000, "time_window_min": None,
           "heartbeat_min": 5.0, "stall_min": 15.0, "ctx_tokens": 24000,
           "max_turns": 6, "respawn_max": 2, "skill_path": None,
           "tools_state": None, "channels_path": None, "dry_run": False,
           "max_parallel_tools": 16}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--dry-run":
            out["dry_run"] = True
            i += 1
            continue
        if tok not in _KNOWN:
            sys.stderr.write("未知参数: %s\n%s\n" % (tok, USAGE))
            raise SystemExit(2)
        if i + 1 >= len(argv):
            sys.stderr.write("参数缺值: %s\n%s\n" % (tok, USAGE))
            raise SystemExit(2)
        key = _KNOWN[tok]
        val = argv[i + 1]
        if key in ("max_intents", "lease_min", "token_cap", "max_turns",
                   "respawn_max", "max_parallel_tools"):
            out[key] = int(val)
        elif key in ("heartbeat_min", "stall_min", "ctx_tokens"):
            out[key] = float(val)
        elif key == "time_window_min":
            out[key] = float(val) if val else None
        else:
            out[key] = val
        i += 2
    for req in ("goal_dir", "battle_name", "max_intents"):
        if not out.get(req):
            sys.stderr.write("缺少必填 --%s\n%s\n"
                             % (req.replace("_", "-"), USAGE))
            raise SystemExit(2)
    return out


def _load_channels(path):
    try:
        with open(path, encoding="utf-8") as f:
            channels = json.load(f)
    except (OSError, ValueError) as e:
        sys.stderr.write("环境问题: channels 文件不可读/非法 JSON (%s): %s\n"
                         % (path, e))
        raise SystemExit(2)
    if not isinstance(channels, list) or not channels:
        sys.stderr.write("环境问题: channels 须非空 JSON 数组: %s\n" % path)
        raise SystemExit(2)
    for c in channels:
        if not isinstance(c, dict) or not (c.get("name") and
                                           c.get("base_url")):
            sys.stderr.write("环境问题: 通道缺 name/base_url: %r\n" % (c,))
            raise SystemExit(2)
    return channels


def build_loop(args, clock=None, tool_spawn=None):
    """装配 WarriorLoop（llmpool_wire.attach 钉根 goal 账本）。"""
    from ledger import llmpool_wire
    if args["dry_run"]:
        channels = [{"name": "dry-run", "model": "dry-run",
                     "base_url": "http://127.0.0.1:1/v1", "api_key": ""}]
    else:
        channels = _load_channels(args["channels_path"])
    pool = llmpool_wire.attach(args["goal_dir"], env=dict(os.environ))
    return loop_mod.WarriorLoop(
        args["goal_dir"], args["battle_name"], channels, pool,
        warrior_id=args["warrior_id"], max_intents=args["max_intents"],
        max_turns=args["max_turns"], lease_min=args["lease_min"],
        token_cap=args["token_cap"],
        time_window_min=args["time_window_min"],
        heartbeat_min=args["heartbeat_min"], stall_min=args["stall_min"],
        ctx_tokens=int(args["ctx_tokens"]), skill_path=args["skill_path"],
        clock=clock, tool_spawn=tool_spawn,
        tool_state_path=args["tools_state"],
        max_parallel_tools=int(args["max_parallel_tools"]))


def run_with_respawn(loop_factory, respawn_max):
    """停滞→重建新循环至优雅停或重生耗尽（退出码 0/3）。"""
    attempts = respawn_max + 1
    for i in range(attempts):
        rep = loop_factory(i).run()
        if rep.status != "stalled":
            return 0
        sys.stderr.write("warrior stalled（第 %d/%d 次重生）: %s\n"
                         % (i + 1, attempts, rep.stop_detail))
    return 3


def main(argv):
    args = parse_args(argv)
    if not os.path.isdir(args["goal_dir"]):
        sys.stderr.write("环境问题: goal 目录不存在 %s\n" % args["goal_dir"])
        return 2
    if not args["dry_run"] and not args["channels_path"]:
        sys.stderr.write("缺 --channels（或 --dry-run）\n%s\n" % USAGE)
        return 2
    if args["dry_run"]:
        lp = build_loop(args)
        results = lp.dry_run()
        if not results:
            sys.stdout.write("(无可领意图——claimable frontier 空)\n")
            return 0
        for r in results:
            sys.stdout.write(r.text + "\n")
        return 0
    return run_with_respawn(lambda i: build_loop(args),
                            args["respawn_max"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
