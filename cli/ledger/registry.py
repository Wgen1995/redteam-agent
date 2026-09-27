# -*- coding: utf-8 -*-
"""命令注册器：各 *_cmds.py 模块导出 HANDLERS = {name: callable(goal_dir, args)->exit_code}；
入口经 lookup 派发。模块缺失（施工中间态）自动跳过。"""
import importlib

_MODULES = ["write_cmds", "query_cmds", "check_cmds", "special", "matrix_init", "graph_cmds"]

# 写命令模块注册表单源（批次 7 T2，C1 并发半边；台账「写命令锁覆盖 18/19 缺失」并入）——
# WRITE_COMMANDS 自写命令模块的 HANDLERS 键集派生，禁手抄名单：
#   write_cmds=契约 02 写命令组（19 条+双前缀别名）；matrix_init=matrix-init（写
#   matrix.tsv+timeline.tsv，金样写面 20 的另一条）。
# R-T2-2：set-replay-state（check_cmds）读写双态同入口，写形锁覆盖留 v3（拆读写形
# 涉契约面，b7 台账登记）；builtin 三条与 query/check/special/graph 各命令=只读不锁。
_WRITER_MODULES = ("write_cmds", "matrix_init")


def _write_commands():
    names = set()
    for m in _WRITER_MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        names |= set(getattr(mod, "HANDLERS", {}))
    return frozenset(names)


_WRITE_COMMANDS = None


def _locked(h):
    """写命令锁包装（分发单点接线）：goal 级写锁包住「读表→改内存→commit」全程。"""
    def wrapper(goal_dir, rest):
        from .filelock import goal_lock
        with goal_lock(goal_dir):
            return h(goal_dir, rest)
    return wrapper


def lookup(cmd):
    global _WRITE_COMMANDS
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
    if _WRITE_COMMANDS is None:
        _WRITE_COMMANDS = _write_commands()
    locked = cmd in _WRITE_COMMANDS
    for m in _MODULES:
        try:
            mod = importlib.import_module("ledger." + m)
        except ImportError:
            continue
        h = getattr(mod, "HANDLERS", {})
        if cmd in h:
            return _locked(h[cmd]) if locked else h[cmd]
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
