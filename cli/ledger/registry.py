# -*- coding: utf-8 -*-
"""命令注册器：各 *_cmds.py 模块导出 HANDLERS = {name: callable(goal_dir, args)->exit_code}；
入口经 lookup 派发。模块缺失（施工中间态）自动跳过。"""
import importlib

_MODULES = ["write_cmds", "query_cmds", "check_cmds", "special"]

def lookup(cmd):
    from . import core

    def _validate(goal_dir, rest):
        return core.cmd_validate(goal_dir)

    def _chain(goal_dir, rest):
        return core.cmd_verify_chain(goal_dir)

    def _next_id(goal_dir, rest):
        if len(rest) != 3:
            raise ValueError("next-id 需 <table> <prefix> <goal-id>")
        return core.cmd_next_id(goal_dir, rest[0], rest[1], rest[2])

    builtin = {"validate": _validate, "verify-chain": _chain, "next-id": _next_id}
    if cmd in builtin:
        return builtin[cmd]
    for m in _MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        h = getattr(mod, "HANDLERS", {})
        if cmd in h:
            return h[cmd]
    return None
