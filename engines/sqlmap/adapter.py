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
import re
import shutil
import sys
from urllib.parse import urlsplit

USAGE = ("用法: adapter.py --intent-id=I --out-dir=D (--plan --target=URL [旋钮] | "
         "--log-file=F | --run --goal-dir=G --target=URL [旋钮])\n"
         "旋钮: --param=P --level=N --risk=N --delay=S --database=DB --table=T "
         "--dbs=A,B --tables=A,B --approval=APR-id --sqlmap=BIN --timestamp=T\n")

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


def verify_approval(goal_dir, ap_id, chash):
    """L3 审批行核验（只读 goal 账本——引擎不写，单写者纪律）。

    approvals.tsv 七列（契约 01）：id/command_hash/decision/approver/timestamp/note/
    schema_version；同 id 取最新行（改判语义，ctx.latest 同口径）。缺文件/畸形行/
    行缺=缺省拒（fail-closed——审批是放行门，宽容方向只能是拒）。
    返回 (ok, reason)。"""
    if not goal_dir:
        return False, "审批核验缺 --goal-dir（审批行只读 goal 账本，无从核验）"
    path = os.path.join(goal_dir, "approvals.tsv")
    row = None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                cells = ln.rstrip("\n").split("\t")
                if len(cells) >= 4 and cells[0] == ap_id:
                    row = cells   # 后行覆盖前行=最新行胜
    except OSError:
        return False, "审批缺省拒: approvals.tsv 不可读（%s）" % path
    if row is None:
        return False, "审批缺省拒: %s 无行（先 tanyin-ledger approve 落 approved 行）" % ap_id
    if row[2] != "approved":
        return False, "审批缺省拒: %s decision=%s（须 approved）" % (ap_id, row[2])
    if row[1] != chash:
        return False, ("审批缺省拒: %s command_hash 不符（行=%s… 计划=%s…——逐条审批"
                       "锚，批的就是这条命令）" % (ap_id, row[1][:12], chash[:12]))
    return True, ""


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
    if needs_approval:
        if not a.get("--approval"):
            return {"wall": "blocked", "needs_approval": True,
                    "reason": ("L3 审批缺省拒: level=%d risk=%d database=%s table=%s 须"
                               " --approval=APR-… 指向 approved 行（command_hash=%s 计划命令: %s）"
                               % (level_v, risk_v, database or "-", table or "-", chash, canonical)),
                    "argv": [], "canonical": canonical, "command_hash": chash}
        ok, why = verify_approval(a.get("--goal-dir", ""), a["--approval"], chash)
        if not ok:
            return {"wall": "blocked", "needs_approval": True, "reason": why,
                    "argv": [], "canonical": canonical, "command_hash": chash}
    return {"wall": "pass", "reason": "", "argv": argv, "canonical": canonical,
            "command_hash": chash, "needs_approval": needs_approval}


def _blocked_plan(reason):
    return {"wall": "blocked", "reason": reason, "argv": [], "canonical": "",
            "command_hash": "", "needs_approval": False}


# ------------------------------------------------------------- 结果解析（findings 队列）

# 运行期命中行：[INFO] GET parameter 'id' is '<technique>' injectable[, for 'MySQL']
INJ_RT = re.compile(r"(?:(GET|POST|PUT|URI|Cookie|User-Agent|header)\s+)?"
                    r"parameter '([^']+)' is '([^']+)' injectable(?:, for '([^']+)')?")
# 收尾汇总块：Parameter: id / 缩进 Type:/Title:/Payload: 四行族
PARAM_SUM = re.compile(r"^Parameter:\s*(\S+)\s*$")
SUM_FIELD = re.compile(r"^\s+(Type|Title|Payload):\s+(.+)$")
DBMS_LINE = re.compile(r"the back-end DBMS is (.+?)\s*$")
NEG_LINE = "all tested parameters do not appear to be injectable"


def parse_log(text):
    """sqlmap 控制台 log → [(place, param, tech, dbms)] + payload 表 + dbms + 负面。

    运行期行与收尾汇总块双源合并（同 place:param 并技法、payload 取汇总块原文）；
    「does not seem to be injectable」类半负面不在此列（仅全否定行算负面事实）。"""
    inj, payloads, dbms, negative = {}, {}, "", False
    cur_param, place_of = None, {}
    for ln in (text or "").splitlines():
        m = INJ_RT.search(ln)
        if m:
            place, param, tech, db = m.group(1) or "", m.group(2), m.group(3), m.group(4)
            inj.setdefault((place, param), {"techs": [], "dbms": ""})
            slot = inj[(place, param)]
            if tech not in slot["techs"]:
                slot["techs"].append(tech)
            if db:
                slot["dbms"] = db
            place_of.setdefault(param, place)
            continue
        if NEG_LINE in ln:
            negative = True
            continue
        m = DBMS_LINE.search(ln)
        if m and not dbms:
            dbms = m.group(1)
            continue
        m = PARAM_SUM.match(ln)
        if m:
            cur_param = m.group(1)
            continue
        m = SUM_FIELD.match(ln)
        if m and cur_param:
            kind, val = m.group(1), m.group(2).strip()
            if kind == "Payload":
                place = place_of.get(cur_param, "")
                payloads.setdefault((place, cur_param), val)
    return inj, payloads, dbms, negative


def normalize(text, intent_id, evidence_ref):
    """解析结果 → 统一提交 schema（契约 07 九字段；引擎只提议 dedup_key）。"""
    inj, payloads, dbms, negative = parse_log(text)
    findings = []
    for (place, param), slot in sorted(inj.items()):
        techs = slot["techs"]
        shown = "、".join(techs[:2]) + ("等" if len(techs) > 2 else "")
        payload = payloads.get((place, param), "")
        steps = ["sqlmap 受控档复扫（--plan/--run 同源参数墙：--batch --delay 强制 --threads=1）"]
        if payload:
            steps.append("Payload: " + payload)
        findings.append({
            "title": "SQL注入 %s参数 %s（%s）" % (place or "", param, shown),
            "confidence": "C3", "impact": "高", "exploitation_status": "suspected",
            "auth_context": "", "reproducible_steps": steps,
            "evidence_refs": [evidence_ref],
            "location": "%s参数 %s" % (place or "参数", param),
            "dedup_key_proposed": "%s:%s+sqlmap" % (place, param),
            "network_position": "internet",
            "preconditions": ["目标可达（internet 视角）", "注入点=%s参数 %s" % (place or "?", param)]
            + (["back-end DBMS: " + slot["dbms"]] if slot["dbms"] else []),
            "expected_matcher": {"matchers": [{"type": "word", "words": ["injectable"]}]},
        })
    facts = []
    if dbms:
        facts.append({"kind": "info", "target": "back-end DBMS",
                      "detail": "识别: " + dbms, "confidence": 0.9})
    if negative or not findings:
        detail = ("全部测试参数不可注入（" + NEG_LINE + "）——负面结果如实入账不静默"
                  if negative else "本次输出未见注入命中行")
        facts.append({"kind": "info", "target": "sqlmap", "detail": detail,
                      "confidence": 0.8})
    return {"intent_id": intent_id, "engine": "sqlmap",
            "status": "done" if findings else "no-findings",
            "facts": facts, "findings": findings, "assets": [], "edges": [],
            "creds": [], "operations_log": "operations.log"}


def _blocked_sub(intent_id):
    return {"intent_id": intent_id, "engine": "sqlmap", "status": "blocked",
            "facts": [], "findings": [], "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}


def _dump(sub, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sub, f, ensure_ascii=False, indent=1, sort_keys=True)


def _timeline_ts(goal_dir):
    """guard 通道时戳：timeline 末行只读回取（确定性投影；禁 datetime.now 进产物）。"""
    try:
        rows = open(os.path.join(goal_dir, "timeline.tsv"), encoding="utf-8",
                    errors="replace").read().splitlines()
    except OSError:
        return ""
    # timeline.tsv 列序（契约 01）：seq/timestamp/event/actor/phase/revert/hash——
    # 取末行第二列；畸形行宽容跳过（空串=上层 blocked，不猜时戳）。
    for ln in reversed(rows):
        cells = ln.split("\t")
        if len(cells) >= 2 and cells[1]:
            return cells[1]
    return ""


def main(argv):
    args = parse_argv(argv)
    for k in ("--intent-id", "--out-dir"):
        if not args.get(k):
            sys.stderr.write(USAGE)
            return 2
    os.makedirs(args["--out-dir"], exist_ok=True)
    log = open(os.path.join(args["--out-dir"], "operations.log"), "w",
               encoding="utf-8", newline="\n")
    sub_path = os.path.join(args["--out-dir"], "submission.json")
    if "--plan" in args:
        plan = plan_profile(args)
        log.write("plan: wall=%s reason=%s\ncanonical: %s\n"
                  % (plan["wall"], plan["reason"], plan["canonical"]))
        print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
        return 0
    if args.get("--log-file"):
        text = open(args["--log-file"], encoding="utf-8", errors="replace").read()
        sub = normalize(text, args["--intent-id"], os.path.basename(args["--log-file"]))
        _dump(sub, sub_path)
        log.write("normalize: findings=%d facts=%d source=%s\n"
                  % (len(sub["findings"]), len(sub["facts"]), args["--log-file"]))
        print("OK submission.json status=%s findings=%d" % (sub["status"], len(sub["findings"])))
        return 0
    if "--run" in args:
        plan = plan_profile(args)   # 墙先于一切执行（计划→审批→环境→执行）
        if plan["wall"] != "pass":
            _dump(_blocked_sub(args["--intent-id"]), sub_path)
            log.write("wall: BLOCKED %s\n" % plan["reason"])
            print("OK submission.json status=blocked reason=%s"
                  % " ".join(plan["reason"].split())[:120])
            return 0
        binary = args.get("--sqlmap", "") or shutil.which("sqlmap")
        if not binary or not os.path.isfile(binary):
            _dump(_blocked_sub(args["--intent-id"]), sub_path)
            log.write("env: sqlmap 可执行缺失（运行时绝不自动安装——契约 10 §4）\n")
            print("OK submission.json status=blocked reason=sqlmap-missing")
            return 0
        ts = args.get("--timestamp", "") or _timeline_ts(args.get("--goal-dir", ""))
        if not ts:
            _dump(_blocked_sub(args["--intent-id"]), sub_path)
            log.write("env: guard 通道时戳不可得（--timestamp 或 timeline 末行）\n")
            print("OK submission.json status=blocked reason=timestamp-unavailable")
            return 0
        guard = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "cli", "tanyin-guard")
        cmd = [sys.executable, guard, "exec", "--goal-dir", args["--goal-dir"],
               "--timestamp=" + ts, "--timeout=600", "--", binary] + plan["argv"][1:]
        log.write("run: %s\ncanonical: %s\n" % (" ".join(cmd), plan["canonical"]))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                           encoding="utf-8", errors="replace")
        outl = os.path.join(args["--out-dir"], "sqlmap-output.log")
        with open(outl, "w", encoding="utf-8", newline="\n") as f:
            f.write(r.stdout)
        log.write("exit=%d\n" % r.returncode)
        if r.returncode != 0:
            _dump(_blocked_sub(args["--intent-id"]), sub_path)
            print("OK submission.json status=blocked reason=guard-exit-%d" % r.returncode)
            return 0
        sub = normalize(r.stdout, args["--intent-id"], "sqlmap-output.log")
        _dump(sub, sub_path)
        log.write("normalize: findings=%d\n" % len(sub["findings"]))
        print("OK submission.json status=%s findings=%d" % (sub["status"], len(sub["findings"])))
        return 0
    sys.stderr.write(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
