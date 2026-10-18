# -*- coding: utf-8 -*-
"""preauth——预授权白名单+超时保守（功能19补件·审批降噪闭环）。

设计权威 docs/design/2026-10-20-command-approval-design.md 补件二：
  ④预授权档：goal 目录 preauth.tsv（操作类+参数约束+有效期；无表头 TSV，
    id 前缀 PA-、schema_version 尾列——格式对齐审批既有表族 approvals.tsv）。
    白名单内=零打扰放行入账：走既有 approve 通道 decision=exempted 且 note
    含原事件文本（query_cmds._replay_status 同判定即刻出队——审批中心/拦截
    页/清理单三面同步消失）；界外/高危/过期=不豁免，永远问。
  ⑤超时保守：待审挂起超 N 分钟（approval.json timeout_min 可配，缺省 30）
    → 保守跳过该操作+记账（approve 通道 decision=rejected，approver=超时
    保守策略，note 含原事件=可对账）+通知（timeline approval-timeout 行）
    ——不卡战线（好停不重启律的审批面）。

舰间契约：本文件=本舰独写；一切 approvals 写经 registry.lookup("approve")
（goal 写锁包装既有执法链——planner_loop 同先例），不碰 write_cmds。
HMAC 兼容：TANYIN_APPROVAL_KEY 在场=approve 须 --sig（同式
HMAC-SHA256(sha256(key), command_hash)——write_cmds._approval_sig 单源语义，
server.py:140 同形复制先例）；本模块照签，test_p0_approval_hmac 不破坏。
纯 stdlib、3.9 兼容；时钟可注入（sweep(now=ISO)——测试确定性）。
"""
import contextlib
import datetime
import hashlib
import hmac
import io
import json
import os

from . import core, query_cmds, registry, timeline

PREAUTH_TSV = "preauth.tsv"
COLS = ("id", "op_class", "param_constraint", "valid_from", "valid_until",
        "approver", "note", "schema_version")
OP_CLASSES = ("read-probe", "retry-same")
CONFIG_JSON = "approval.json"
DEFAULT_TIMEOUT_MIN = 30
ENV_KEY = "TANYIN_APPROVAL_KEY"
ACTOR_NOTIFY = "总控"

# 只读动词/高危记号（确定性词表推导——审批中心 AI 预审同先例，不上模型）
_READ_VERBS = ("http-get", "https-get", "curl", "wget", "dig", "nslookup",
               "whois", "nmap -sv", "nmap -st", "get ", "head ", "probe-read")
_DANGER_MARKS = ("rm -f", "rm -rf", "mkfs", "drop ", "upload", "inject",
                 "egress", "deploy", "shutdown", "reboot", "破坏", "越权",
                 "写操作", "删除")


# ---------------------------------------------------------------- 读表白名单 --

def read_preauth(goal_dir):
    """preauth.tsv → [dict]（无表头行式；缺文件/坏行=跳过不炸）。"""
    path = os.path.join(goal_dir, PREAUTH_TSV)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        cols = (cols + [""] * len(COLS))[:len(COLS)]
        out.append(dict(zip(COLS, cols)))
    return out


def _parse_ts(text):
    try:
        return datetime.datetime.strptime(str(text).strip(),
                                          "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def _constraint(param):
    """参数约束串 → dict（scope=域名 / max=次数；多段分号分隔）。"""
    out = {}
    for part in str(param or "").split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            out[k.strip()] = v.strip()
    return out


def match_entry(entry, event, revert_cmd, same_count=1, now=None):
    """单条预授权 vs 一条待审操作 → (是否放行, 人话理由)。

    判序：效期窗 → 操作类分支（read-probe=只读动词+无高危记号+界内；
    retry-same=同参数重试次数≤max）。任何一环不满足=不放行（永远问）。
    """
    now_dt = _parse_ts(now) if now else datetime.datetime.utcnow()
    vf, vu = _parse_ts(entry.get("valid_from")), _parse_ts(entry.get("valid_until"))
    if now_dt is None or vf is None or vu is None:
        return False, "有效期格式不对——按保守不豁免"
    if not (vf <= now_dt <= vu):
        return False, "不在有效期内——按保守不豁免"
    text = (str(event) + " " + str(revert_cmd)).lower()
    cons = _constraint(entry.get("param_constraint"))
    op = str(entry.get("op_class") or "")
    if op == "read-probe":
        if any(m in text for m in _DANGER_MARKS):
            return False, "含高危或不可逆动作——必须人工审"
        if not any(v in text for v in _READ_VERBS):
            return False, "不是已知的只读动作——必须人工审"
        scope = cons.get("scope", "")
        if scope and scope.lower() not in text:
            return False, "目标不在预授权范围内——必须人工审"
        return True, "界内只读探测——预授权零打扰放行"
    if op == "retry-same":
        try:
            cap = int(cons.get("max", "0"))
        except ValueError:
            return False, "max 约束格式不对——按保守不豁免"
        if cap < 1:
            return False, "max 约束须≥1——按保守不豁免"
        if same_count <= cap:
            return True, "同参数重试第 %d 次≤%d——预授权零打扰放行" % (
                same_count, cap)
        return False, "同参数重试超过 %d 次——必须人工审" % cap
    return False, "未知操作类——必须人工审"


# ---------------------------------------------------------------- 配置与钥匙 --

def load_timeout(goal_dir, override=None):
    """超时帽（分钟）：显式参 > goal 目录 approval.json timeout_min > 缺省 30。"""
    if override is not None:
        return int(override)
    try:
        with open(os.path.join(goal_dir, CONFIG_JSON), encoding="utf-8") as f:
            doc = json.load(f)
        return int(doc.get("timeout_min", DEFAULT_TIMEOUT_MIN))
    except (OSError, ValueError, TypeError):
        return DEFAULT_TIMEOUT_MIN


def _approval_key():
    k = os.environ.get(ENV_KEY, "")
    return k.encode("utf-8") if k else None


def _sig(command_hash, key_bytes):
    """HMAC-SHA256(sha256(key), command_hash)——write_cmds._approval_sig 同式。"""
    return hmac.new(hashlib.sha256(key_bytes).digest(),
                    command_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def _approve(goal_dir, decision, chash, approver, ts, note):
    """走既有 approve 通道（registry.lookup=goal 写锁执法链）→ 回执 id。

    钥在场=照签 --sig（同式 HMAC）；通道拒收=RuntimeError fail-loud。
    """
    argv = ["--command-hash=" + chash, "--decision=" + decision,
            "--approver=" + approver, "--timestamp=" + ts,
            "--note=" + note]
    key = _approval_key()
    if key:
        argv.append("--sig=" + _sig(chash, key))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = registry.lookup("approve")(goal_dir, argv)
    out = buf.getvalue()
    if rc != 0:
        raise RuntimeError("approve 通道拒收: " + out.strip()[:200])
    first = out.splitlines()[0] if out.splitlines() else ""
    return first.split("\t")[1] if first.startswith("OK\t") else ""


def _same_count(tl_rows, revert_cmd):
    return sum(1 for r in tl_rows
               if len(r) > 4 and r[4].strip() == str(revert_cmd).strip())


# ---------------------------------------------------------------- 主入口 --

def sweep(goal_dir, now=None, timeout_min=None):
    """降噪一轮：白名单零打扰豁免 + 挂起超时保守跳过 → 人话回执。

    判序：先白名单（界内只读/限次重试即刻出队），落不下且等超帽的按保守
    跳过（rejected+通知行）；新鲜待审不动。写全经 approve 通道，幂等
    （已豁免/已决的行 _replay_status 不再列 pending）。
    """
    ts = str(now) if now else datetime.datetime.utcnow().strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    now_dt = _parse_ts(ts) or datetime.datetime.utcnow()
    tmo = load_timeout(goal_dir, override=timeout_min)
    s = core.Session(goal_dir)
    tl = s.rows("timeline.tsv")
    entries = read_preauth(goal_dir)
    exempted, timed_out = [], []
    for idx, it in enumerate([x for x in query_cmds._replay_status(s)
                              if x["status"] == "pending"]):
        r = it["row"]
        ev, rv, row_ts = r[3], r[4], r[0]
        chash = hashlib.sha256(rv.encode("utf-8")).hexdigest()
        hit = None
        for e in entries:
            ok, why = match_entry(e, ev, rv,
                                  same_count=_same_count(tl, rv), now=ts)
            if ok:
                hit = (e, why)
                break
        if hit is not None:
            e, why = hit
            _approve(goal_dir, "exempted", chash,
                     "预授权白名单:" + e.get("id", "?"), ts,
                     "预授权零打扰放行（%s） 原事件:%s" % (why, ev))
            exempted.append({"row": tl.index(r) + 1, "event": ev,
                             "preauth_id": e.get("id", "?"), "reason": why})
            continue
        made = _parse_ts(row_ts)
        if made is None:
            continue                          # 坏钟=按保守不自动决定
        waited = int((now_dt - made).total_seconds() // 60)
        if waited >= tmo:
            _approve(goal_dir, "rejected", chash, "超时保守策略", ts,
                     "超时%d分钟 保守跳过该操作 原事件:%s" % (waited, ev))
            timeline.append_tl_locked(
                goal_dir, ts,
                "approval-timeout row=%d waited=%dm skipped=1 原事件:%s"
                % (tl.index(r) + 1, waited, ev),
                actor=ACTOR_NOTIFY, phase="P3")
            timed_out.append({"row": tl.index(r) + 1, "event": ev,
                              "waited_min": waited})
    return {"exempted": exempted, "timed_out": timed_out,
            "timeout_min": tmo,
            "note": ("降噪一轮：零打扰放行 %d 条；超时保守跳过 %d 条（帽=%d分钟）"
                     % (len(exempted), len(timed_out), tmo))}
