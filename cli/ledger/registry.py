# -*- coding: utf-8 -*-
"""命令注册器：各 *_cmds.py 模块导出 HANDLERS = {name: callable(goal_dir, args)->exit_code}；
入口经 lookup 派发。模块缺失（施工中间态）自动跳过。"""
import importlib

_MODULES = ["write_cmds", "query_cmds", "check_cmds", "special", "matrix_init"]

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


def all_commands():
    """枚举 41 命令基名——引擎「九门断言命令存在性」检查的单源（批次 3 T2）。

    HANDLERS 里的 ledger- 前缀键分两种：有无前缀孪生键的=双前缀注册别名（剔出基名集，
    如 ledger-add-goal之于add-goal）；无孪生的=原生名本就带前缀的四条校验命令
    （ledger-scope-coverage/ledger-tree-check/ledger-replay-summary/ledger-terminal-gate，
    计入基名）。builtin 三条（validate/verify-chain/next-id）一并计入——合计 41。"""
    names = {"validate", "verify-chain", "next-id"}
    keys = set()
    for m in _MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        keys |= set(getattr(mod, "HANDLERS", {}))
    for k in keys:
        if k.startswith("ledger-") and k[len("ledger-"):] in keys:
            continue   # 双前缀别名，非基名
        names.add(k)
    return names
