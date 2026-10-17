#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sqlmap 受控档适配器（W3-P1-1①，契约 07/08）——只读检测档→统一提交 schema。

docs/reviews/2026-10-17-exceed-review/03-渗透工作流专家.md P1-1「sqlmap OSD 受控
档位（--level/--risk 由 permitted_actions+L3 审批门控）」的引擎面落地。参数墙五件
（全部机械执法，argv 只由白名单旋钮拼装、**无透传通道**——写/外带面旗标结构性
不可达，不靠调用方自觉）：

1 --delay 强制：缺省注入 1s，墙区间 [0.5, 60]（下限=防锤击；上限=异常值拒收）。
2 禁碰端口：目标 URL 命中 FORBIDDEN_PORTS（8900/3000/8787/8443）=墙拒（交战纪律
  单源同值，vulnclaw 适配器同款口径）。
3 受控顶：--level≤3/--risk≤2（guard deny-list 已拦 --level=5/--risk=3，引擎侧更紧；
  越顶=墙拒，审批不可救——上限就是上限）。
4 限库限表：-D 须在 --dbs 白名单（缺省零白名单=零库可碰，fail-closed）；-T 须伴
  -D 且在 --tables 白名单。
5 只读检测档：--dump/--os-shell/--sql-query/--read-file 等数据面旗标不在旋钮表内，
  终检再扫一遍 FORBIDDEN_ARGS（纵深防御——防后续改动加旋钮时破档）。

L3 审批挂接（Cycle B）：--level>1 / --risk>1 / 任何 -D/-T 枚举请求 ⇒ 须
--approval=APR-… 指向 goal 目录 approvals.tsv 的 approved 行且 command_hash 与
计划命令 sha256 一致（逐条审批锚），缺省拒。

三运行面：--plan（墙预检+计划命令打印，零执行零提交产物）；--log-file（离线
归一化 canned sqlmap 控制台输出）；--run --goal-dir（经 tanyin-guard exec 执行
通道）。引擎不写账本（单写者，契约 07 §4）。
"""
import hashlib
import json
import os
import sys
from urllib.parse import urlsplit

USAGE = ("用法: adapter.py --intent-id=I --out-dir=D (--plan --target=URL [旋钮] | "
         "--log-file=F | --run --goal-dir=G --target=URL [旋钮])\n"
         "旋钮: --param=P --level=N --risk=N --delay=S --database=DB --table=T "
         "--dbs=A,B --tables=A,B --approval=APR-id --sqlmap=BIN\n")

# 交战纪律禁碰端口（cli/ledger 同源口径；vulnclaw 适配器同款落地）
FORBIDDEN_PORTS = (8900, 3000, 8787, 8443)
# 受控档位顶（guard deny-list 拦 --level=5/--risk=3；引擎顶更紧）
MAX_LEVEL, MAX_RISK = 3, 2
# --delay 墙区间（秒）：下限=防锤击，上限=异常值拒收
DELAY_FLOOR, DELAY_CEIL, DELAY_DEFAULT = 0.5, 60.0, 1.0
# 只读检测档禁令集：数据外带/写面/交互 shell/注册表/凭据枚举——旋钮表不收录 +
# 终检再扫（纵深防御）。缺省档即最高档：这些旗标任何组合都不可达。
FORBIDDEN_ARGS = (
    "--dump", "--dump-all", "--search", "--os-shell", "--os-cmd", "--os-pwn",
    "--os-smbrelay", "--os-bof", "--priv-esc", "--sql-shell", "--sql-query",
    "--eval", "--read-file", "--write-file", "--file-upload", "--file-dest",
    "--reg-read", "--reg-add", "--reg-del", "--passwords", "--users",
    "--privileges", "--roles", "--takeover-outfile",
)


def parse_argv(argv):
    """--key=value 与 --key value 双形态归一（T5 裁决②同款 argv 契约）。"""
    args, i = {}, 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            if "=" in a:
                args.setdefault(a.partition("=")[0], a.partition("=")[2])
                i += 1
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args.setdefault(a, argv[i + 1])
                i += 2
            else:
                args.setdefault(a, "")
                i += 1
        else:
            i += 1
    return args


def _int_in(tok, lo, hi):
    try:
        v = int(tok)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def _delay_ok(tok):
    try:
        v = float(tok)
    except (TypeError, ValueError):
        return None
    return v if DELAY_FLOOR <= v <= DELAY_CEIL else None


def _whitelist(tok):
    """逗号白名单 → 小写集合（strip 空容差；比对一律小写=宽度一致严格）。"""
    return {x.strip().lower() for x in (tok or "").split(",") if x.strip()}


def _target_port(target):
    try:
        return urlsplit(target).port
    except ValueError:
        return None


def plan_profile(a):
    """参数墙单源：旋钮 dict → 计划。返回
    {wall: pass|blocked, reason, argv, canonical, command_hash, needs_approval}。
    argv 只由白名单旋钮拼装（未知旗标不透传），终检扫 FORBIDDEN_ARGS 纵深防御。
    墙序：target/禁碰端口 → delay → 受控顶 → 限库限表 → 数据面终检 →（needs_approval
    标记，审批本体的核验在 Cycle B）。"""
    target = a.get("--target", "")
    if not target:
        return _blocked_plan("缺 --target（受控档无免目标运行）")
    port = _target_port(target)
    if port in FORBIDDEN_PORTS:
        return _blocked_plan("目标端口 %d 在禁碰清单 8900/3000/8787/8443（交战纪律）" % port)
    # 墙 1：--delay 强制（缺省注入；越 [0.5,60] 拒收）
    delay_tok = a.get("--delay", "") or str(DELAY_DEFAULT)
    delay_v = _delay_ok(delay_tok)
    if delay_v is None:
        return _blocked_plan("delay=%s 越墙区间 [%.1f, %.0f]（防锤击下限/异常值上限）"
                             % (delay_tok, DELAY_FLOOR, DELAY_CEIL))
    # 墙 3：受控顶（越顶=墙拒，审批不可救）
    level_tok = a.get("--level", "") or "1"
    level_v = _int_in(level_tok, 1, MAX_LEVEL)
    if level_v is None:
        return _blocked_plan("level=%s 越受控顶（1-%d；%d+ 须经专项裁决，审批不可救）"
                             % (level_tok, MAX_LEVEL, MAX_LEVEL + 1))
    risk_tok = a.get("--risk", "") or "1"
    risk_v = _int_in(risk_tok, 1, MAX_RISK)
    if risk_v is None:
        return _blocked_plan("risk=%s 越受控顶（1-%d）" % (risk_tok, MAX_RISK))
    # 墙 4：限库限表（缺省零白名单=零库可碰）
    dbs, tables = _whitelist(a.get("--dbs", "")), _whitelist(a.get("--tables", ""))
    database = a.get("--database", "")
    table = a.get("--table", "")
    if database and database.strip().lower() not in dbs:
        return _blocked_plan(
            "库白名单拒收: -D %s 不在 --dbs=%s（缺省零白名单=零库可碰，fail-closed）"
            % (database, ",".join(sorted(dbs)) or "(空)"))
    if table and not database:
        return _blocked_plan("表白名单拒收: --table 须伴 --database（先锁库再锁表）")
    if table and table.strip().lower() not in tables:
        return _blocked_plan("表白名单拒收: -T %s 不在 --tables=%s"
                             % (table, ",".join(sorted(tables)) or "(空)"))
    # argv 拼装：只收白名单旋钮（结构性无透传）
    argv = ["sqlmap", "-u", target, "--batch",
            "--delay=%g" % delay_v, "--threads=1", "--timeout=30", "--retries=2"]
    if a.get("--param"):
        argv += ["-p", a["--param"]]
    argv += ["--level=%d" % level_v, "--risk=%d" % risk_v]
    if database:
        argv += ["-D", database]
    if table:
        argv += ["-T", table]
    # 墙 5：数据面终检（纵深防御——旋钮表今天产不出这些，防明日改动破档）
    hit = next((t for t in FORBIDDEN_ARGS if t in argv), None)
    if hit:
        return _blocked_plan("只读检测档终检命中禁令旗标: " + hit)
    needs_approval = level_v > 1 or risk_v > 1 or bool(database) or bool(table)
    canonical = " ".join(argv)
    chash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    # L3 审批缺省拒：提级（level>1/risk>1）或任何 -D/-T 枚举请求 ⇒ 须 approved 行
    # 背书（行匹配核验=Cycle B 落位；此处先立「无审批不放行」的门）。审批锚=
    # command_hash（计划命令 sha256，逐条审批——批的就是这条命令，不是意图泛授权）。
    if needs_approval and not a.get("--approval"):
        return {"wall": "blocked", "needs_approval": True,
                "reason": ("L3 审批缺省拒: level=%d risk=%d database=%s table=%s 须"
                           " --approval=APR-… 指向 approved 行（command_hash=%s 计划命令: %s）"
                           % (level_v, risk_v, database or "-", table or "-", chash, canonical)),
                "argv": [], "canonical": canonical, "command_hash": chash}
    return {"wall": "pass", "reason": "", "argv": argv, "canonical": canonical,
            "command_hash": chash, "needs_approval": needs_approval}


def _blocked_plan(reason):
    return {"wall": "blocked", "reason": reason, "argv": [], "canonical": "",
            "command_hash": "", "needs_approval": False}


def main(argv):
    args = parse_argv(argv)
    for k in ("--intent-id", "--out-dir"):
        if not args.get(k):
            sys.stderr.write(USAGE)
            return 2
    if "--plan" in args:
        plan = plan_profile(args)
        print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
        return 0
    sys.stderr.write("W3 分批施工：--log-file/--run 面随后续循环落位\n" + USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
