# -*- coding: utf-8 -*-
"""tanyin-tools 子命令层（W3③：卡片清单命令）。

list 列卡 / show 查卡详情 / install 装卡验签 / uninstall 除役 /
verify-lock 全量验签 / exec 执行入口（必过 gate 门链+guard 委托）。
退出码（house 律）：0=通过 1=门禁失败 2=用法/环境。
铁律 7：语义判断禁入——本层只做机械清单与确定性门禁。
"""
import os
import sys

TAB = chr(9)
LF = chr(10)

from . import cards as tool_cards  # noqa: E402
from . import gate as tool_gate  # noqa: E402
from . import install as tool_install  # noqa: E402
from . import lock as tool_lock  # noqa: E402

SUBCOMMANDS = ("list", "show", "install", "uninstall", "verify-lock", "exec")

USAGE = ("用法: tanyin-tools <子命令> [参数...]" + LF +
         "子命令(6): " + " ".join(SUBCOMMANDS) + LF +
         "  list [--state P]" + LF +
         "  show <卡名>" + LF +
         "  install <卡名> --timestamp=ISO8601 [--state P] [--lock P] [--pub P]" + LF +
         "  uninstall <卡名> [--state P]" + LF +
         "  verify-lock [--lock P] [--pub P]" + LF +
         "  exec --goal-dir D --timestamp=ISO8601 [--state P] [--lock P] [--pub P]" + LF +
         "      -- <卡名> [参数...]")


def _kv(rest):
    """旗标解析：--k=v 与 --k v（值不 startswith 减号）双形；-- 分隔符已剔除。"""
    kv = {}
    pos = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a.startswith("--"):
            if "=" in a:
                k, v = a[2:].split("=", 1)
                kv[k] = v
            elif i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                kv[a[2:]] = rest[i + 1]
                i += 1
            else:
                kv[a[2:]] = ""
        else:
            pos.append(a)
        i += 1
    return kv, pos


def _state_of(kv):
    return kv.get("state") or None


def cmd_list(kv, pos):
    state = _state_of(kv)
    rows = []
    for c in sorted(tool_cards.all_cards(), key=lambda x: x.name):
        ins = "in-service" if tool_install.is_installed(c, state_path=state) else "-"
        rows.append(TAB.join([c.name, c.tier, c.rate, c.risk, c.category, ins]))
    out = [TAB.join(["name", "tier", "rate", "risk", "category", "service"])]
    out += rows
    out.append("cards=%d" % len(rows))
    sys.stdout.write(LF.join(out) + LF)
    return 0


def cmd_show(kv, pos):
    if len(pos) != 1:
        sys.stderr.write("show 需恰一个卡名" + LF)
        return 2
    c = tool_cards.get_card(pos[0])
    if c is None:
        sys.stderr.write("unknown-tool: %s 不在注册表" % pos[0] + LF)
        return 2
    d = c.as_public_dict()
    entries = tool_lock.load()
    e = entries.get(c.name, {})
    lines = [
        "name: " + d["name"],
        "binary: " + d["binary"],
        "tier: " + d["tier"] + ("  [L3 审批门挂卡：approve --command-hash 后方可执行]"
                                if d["requires_approval"] else ""),
        "rate: " + d["rate"] + ("  (固化旗标: " + " ".join(d["rate_flags"]) + ")"
                                if d["rate_flags"] else ""),
        "risk: " + d["risk"],
        "category: " + d["category"],
        "deny_extra: " + (";".join(d["deny_extra"]) or "-"),
        "revert: " + d["revert"],
        "example: " + " ".join(d["example"]),
        "version: " + d["version"],
        "lock: " + (e.get("version", "-") + " " + e.get("sha256", "-")[:12]
                    + " sig=" + ("yes" if e.get("sig") else "no") if e else "-"),
        "summary: " + c.summary,
    ]
    sys.stdout.write(LF.join(lines) + LF)
    return 0


def cmd_install(kv, pos):
    if len(pos) != 1:
        sys.stderr.write("install 需恰一个卡名" + LF)
        return 2
    ts = kv.get("timestamp", "")
    if not ts:
        sys.stderr.write("install 须带 --timestamp=ISO8601（EPOCH 缺省已退役）" + LF)
        return 2
    ok, why = tool_install.install(
        pos[0], ts, state_path=_state_of(kv),
        lock_path=kv.get("lock") or None, pub=kv.get("pub") or None)
    sys.stdout.write(("OK " if ok else "REJECT ") + why + LF)
    return 0 if ok else 1


def cmd_uninstall(kv, pos):
    if len(pos) != 1:
        sys.stderr.write("uninstall 需恰一个卡名" + LF)
        return 2
    tool_install.uninstall(pos[0], state_path=_state_of(kv))
    sys.stdout.write("OK 除役: " + pos[0] + LF)
    return 0


def cmd_verify_lock(kv, pos):
    try:
        results = tool_lock.verify_all(kv.get("lock") or None,
                                       kv.get("pub") or None)
    except (OSError, tool_lock.LockError) as e:
        sys.stderr.write("lock 载入失败: %s" % e + LF)
        return 2
    bad = 0
    for name, ok, why in results:
        if not ok:
            bad += 1
        sys.stdout.write("%s	%s	%s" % (name, "PASS" if ok else "FAIL", why) + LF)
    sys.stdout.write("entries=%d fail=%d" % (len(results), bad) + LF)
    return 1 if bad else 0


def cmd_exec(kv, pos):
    gd = kv.get("goal-dir", "")
    ts = kv.get("timestamp", "")
    if not gd:
        sys.stderr.write("exec 须带 --goal-dir <目录>" + LF)
        return 2
    if not os.path.isdir(gd):
        sys.stderr.write("环境问题: goal 目录不存在" + LF)
        return 2
    if not ts:
        sys.stderr.write("exec 须带 --timestamp=ISO8601（EPOCH 缺省已退役）" + LF)
        return 2
    if not pos:
        sys.stderr.write("exec 需要 -- 后跟 <卡名> [参数...]" + LF)
        return 2
    name, args = pos[0], pos[1:]
    rc, out, err = tool_gate.execute(
        gd, name, args, ts, state_path=_state_of(kv),
        lock_path=kv.get("lock") or None, pub=kv.get("pub") or None)
    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return rc


_HANDLERS = {"list": cmd_list, "show": cmd_show, "install": cmd_install,
             "uninstall": cmd_uninstall, "verify-lock": cmd_verify_lock,
             "exec": cmd_exec}


def main(argv):
    if not argv or argv[0] not in _HANDLERS:
        sys.stderr.write(USAGE)
        return 2
    kv, pos = _kv([a for a in argv[1:] if a != "--"])
    return _HANDLERS[argv[0]](kv, pos)
