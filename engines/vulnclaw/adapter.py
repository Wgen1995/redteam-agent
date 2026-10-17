#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vulnclaw 插槽适配器（W1-T6，契约 08 §5/07）——solve 会话→统一提交 schema。

docs/research/vulnclaw-live-trial.md §10.4 上线前置四件的引擎面落地：
① 消费 final_answer+verified_claims（findings[] 只当线索队列——§10.2④a：模型把
   实证发现写在 FINAL 文本里，findings 商店只有规则层「[自动]」候选，其证据串是
   模板碎片、甚至与模型自己的否定结论相矛盾）。FINAL 段 F 头（F1 · Low/信息泄露 ·
   标题）确定性解析→findings（C2/verified，证据 eNNN 随行，区间 e005–e009 展开）；
   否定结果/未测项/verified_claims→facts（往往更值钱，§10.2②）。
② 副作用黑名单（删库/关机/外发）进 TaskConstraints 预筛（§10.2④b）——
   build_constraints 落 task-constraints.json（VulnClaw TaskConstraints 11 键形状，
   task_service 同款消费）+goal 预筛命中即 blocked（fail-closed），不走 prompt 自觉。
③ 成本走网关侧 usage 外挂回填（§9.5/§10.4④）——引擎内建 usage 计量两轮实测
   requests=0/tokens=0 不可信不采信；--usage-file 网关侧记录求和入 fact+归档，
   缺位如实记缺位（成本核算不静默归零）。
④ 绕 P0#2 findings 组装崩溃（§9.6/§10.4①）——CLI 收尾把 verified_claims（int 计数
   形状，agent_state.get_summary 侧）切片崩在 cli/main.py:1609、complete 事件发不出；
   适配器自身容忍 int 形状，complete 缺席/--run 崩溃签名→改走 session.json 手动归一
   +手动 vulnclaw report（§9.6 实测规避路径），不依赖 CLI 收尾。

引擎不写账本（单写者，契约 07 §4）。离线面：--session 归一化既有会话（测试/复盘）。"""
import json, os, re, shutil, subprocess, sys
from urllib.parse import urlsplit

USAGE = ("用法: adapter.py --intent-id=I --out-dir=D (--session=S [--events-file=E]"
         " [--usage-file=U] | --run --target=URL --goal=G [--config-dir=C]"
         " [--vulnclaw=B] [--usage-file=U])\n")
FORBIDDEN_PORTS = (8900, 3000, 8787, 8443)   # 交战纪律禁碰端口→结构化落地 blocked_ports
SEV2IMPACT = {"critical": "高", "high": "高", "medium": "中", "low": "低", "info": "低"}
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1", "0.0.0.0")

# ② 副作用黑名单三类（§10.2④b）：模式命中 goal 即预筛拦截；「禁止删库」类否定措辞
# 不算命中（_negated 前视窗口内出现禁止词→放过，宽 False 正向漏拦可接受、误拦不可）。
SIDE_EFFECT_BLACKLIST = (
    ("删库", ("drop database", "drop table", "drop schema", "truncate database",
             "truncate table", "删库", "删除数据库", "清空数据库", "rm -rf", "mkfs")),
    ("关机", ("shutdown", "shut down", "reboot", "poweroff", "halt -p", "init 0",
             "init 6", "systemctl poweroff", "systemctl reboot", "关机", "重启服务器",
             "停止生产服务")),
    ("外发", ("exfiltrat", "数据外传", "外发数据", "上传到外部", "发送到外部",
             "传出内网", "回传到外部", "外带数据")),
)
BLOCKED_ACTIONS = ("drop-database", "truncate-table", "destroy-data",
                   "shutdown-host", "reboot-host", "exfiltrate-data")
NEGATORS = ("禁止", "不得", "不许", "不要", "严禁", "勿")

F_HEAD = re.compile(r"\*\*(F\d+)\s*·\s*([^·*]+?)(?:\s*·\s*([^*]+))?\*\*")


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


def _negated(text, idx):
    """命中点前 6 字符窗口内有否定词（禁止删库）→非命中。"""
    return any(n in text[max(0, idx - 6):idx] for n in NEGATORS)


def blacklist_hits(text):
    """② 预筛：goal 文本逐类匹配副作用黑名单，返回 [(类别, 片段)]（小写比对）。"""
    out = []
    low = (text or "").lower()
    for kind, pats in SIDE_EFFECT_BLACKLIST:
        for p in pats:
            start = 0
            while True:
                idx = low.find(p.lower(), start)
                if idx < 0:
                    break
                if not _negated(low, idx):
                    out.append((kind, low[idx:idx + 40]))
                    break
                start = idx + len(p)
    return out


def _split_target(target):
    """http://localhost:3081 → (localhost, 3081)；畸形输入=(原串, None)。"""
    try:
        u = urlsplit(target)
        return u.hostname or "", u.port
    except ValueError:
        return target, None


def build_constraints(target):
    """② VulnClaw TaskConstraints 11 键形状（task_service scope 同款消费面）。"""
    host, port = _split_target(target)
    return {
        "allowed_ports": [port] if port else [],
        "blocked_ports": list(FORBIDDEN_PORTS),
        "allowed_hosts": [host] if host else [],
        "blocked_hosts": [],
        "allowed_paths": [],
        "blocked_paths": [],
        "allowed_actions": [],
        "blocked_actions": list(BLOCKED_ACTIONS),
        "notes": [
            "副作用黑名单（删库/关机/外发）结构化执法：命中即拦，不靠 prompt 措辞"
            "（vulnclaw-live-trial §10.2④b）",
            "锁定类副作用（账号硬锁定）须在报告披露并人工复核（§10.2 F2 教训）",
        ],
        "strict_mode": True,
    }


def _evidence_ids(text):
    """eNNN 引用收集：e005–e009 区间展开（≤60 跨度）+散点；排序去重，≤16。"""
    ids = set()
    for a, b in re.findall(r"e(\d+)\s*[–—-]\s*e(\d+)", text):
        ai, bi = int(a), int(b)
        if bi >= ai and bi - ai <= 60:
            ids.update("e%03d" % i for i in range(ai, bi + 1))
    ids.update("e%03d" % int(x) for x in re.findall(r"(?<![0-9a-zA-Z])e(\d{2,4})(?![0-9])", text))
    return sorted(ids)[:16]


def _clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 1] + "…"


def _location(title, body, target):
    """标题优先取路径锚（/api/health、/@vite/client），缺省回落目标本体。"""
    for txt in (title, " ".join(body[:4])):
        m = re.search(r"(/[A-Za-z0-9_\-./@%]{2,})", txt.replace("`", " "))
        if m:
            return m.group(1)
    return target


def parse_final_answer(text):
    """① FINAL 文本确定性解析：F 头→发现（标题/级别/类型/正文/证据），
    ### 段归类负面结果/未测项/范围合规，FINAL: 行=完成断言。
    返回 (findings, negatives, untested, compliance, final_line)。"""
    fnds, negs, untes, compliance, final_line = [], [], [], "", ""
    cur, section = None, ""
    for ln in (text or "").splitlines():
        h = F_HEAD.search(ln)
        if h:
            cur = {"fid": h.group(1), "sev_raw": h.group(2).strip(),
                   "title": (h.group(3) or "").strip(),
                   "body": [ln[h.end():].lstrip(" ：:")] if ln[h.end():].strip() else []}
            fnds.append(cur)
            continue
        if ln.startswith("#"):                       # ###/## 段头：终结当前 F 收集
            section, cur = ln.lstrip("#").strip(), None
            continue
        if cur is not None:
            cur["body"].append(ln)
            continue
        if ln.startswith("FINAL:"):
            final_line = ln[len("FINAL:"):].strip()
            continue
        s = ln.strip()
        if not s:
            continue
        if "负面" in section or "否定" in section:
            if s.startswith("-"):
                negs.append(s.lstrip("- ").strip())
        elif "剩余" in section or "未测" in section:
            if s.startswith("-"):
                untes.append(s.lstrip("- ").strip())
        elif "合规" in section:
            compliance = _clip(s, 200)
    out = []
    for f in fnds:
        sev, _, vtype = f["sev_raw"].partition("/")
        body = [b for b in f["body"] if b.strip()]
        steps = [b.lstrip("- ").strip() for b in body if b.strip().startswith("-")]
        steps = steps or body
        steps = [_clip(s, 240) for s in steps if s][:8]
        title = f["title"] or _clip((body[0] if body else ""), 48) or f["fid"]
        ev = _evidence_ids(f["title"] + " " + " ".join(body))
        out.append({
            "fid": f["fid"], "title": _clip(title, 160),
            "impact": SEV2IMPACT.get(sev.strip().lower(), "中"),
            "vtype": vtype.strip() or "发现", "steps": steps or
            ["见 final_answer %s 段（证据 %s）" % (f["fid"], ",".join(ev[:6]) or "无")],
            "evidence": ev, "location": _location(f["title"], body, ""),
        })
    return out, negs, untes, compliance, final_line


def load_usage(path):
    """③ 网关侧 usage 外挂：records 列表（或单记录/包一层 dict）求和。
    键名容错：input/prompt、output/completion、total_tokens、cost_usd/cost/dollars；
    requests 缺省按记录数计。"""
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        records = data.get("records") or data.get("usage") or data.get("data") or [data]
    else:
        records = data
    agg = {"requests": 0, "input_tokens": 0, "output_tokens": 0,
           "total_tokens": 0, "dollars": 0.0, "records": 0}
    for r in records:
        if not isinstance(r, dict):
            continue
        i = int(r.get("input_tokens") or r.get("prompt_tokens") or 0)
        o = int(r.get("output_tokens") or r.get("completion_tokens") or 0)
        t = int(r.get("total_tokens") or (i + o))
        c = r.get("cost_usd")
        if c is None:
            c = r.get("cost") if r.get("cost") is not None else r.get("dollars") or 0.0
        agg["requests"] += int(r.get("requests") or 1)
        agg["input_tokens"] += i
        agg["output_tokens"] += o
        agg["total_tokens"] += t
        agg["dollars"] += float(c or 0.0)
        agg["records"] += 1
    return agg


def _complete_present(path):
    """④ stream NDJSON 里有无 {"type":"complete"} 行（P0#2 崩溃则发不出）。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    j = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(j, dict) and j.get("type") == "complete":
                    return True
    except OSError:
        return True                                  # 无事件面可考=不判绕过
    return False


def normalize(session_path, intent_id, log):
    """① 离线归一：session.json（真实形状，docs/research/vulnclaw-live-trial.md §10 样本）
    →统一提交。verified_claims 容忍 int 计数形状（④ P0#2 上游崩点）。"""
    with open(session_path, encoding="utf-8") as f:
        d = json.load(f)
    asx = d.get("agent_state") or {}
    target = d.get("target") or ""
    stem = os.path.basename(session_path)
    host, _p = _split_target(target)
    net_pos = "same-host" if host in LOCAL_HOSTS else "internet"

    claims = asx.get("verified_claims")
    if isinstance(claims, int):
        log.write("P0#2 形状容忍: verified_claims=<int:%d>（get_summary 计数形状——上游"
                  " cli/main.py:1609 对其切片即 TypeError）——本适配器不订阅该形状，"
                  "final_answer 消费不受影响\n" % claims)
        claims = []
    elif not isinstance(claims, list):
        claims = []

    findings, facts, assets = [], [], []
    parsed, negs, untes, compliance, final_line = parse_final_answer(asx.get("final_answer") or "")
    for p in parsed:
        findings.append({
            "title": p["title"],
            "confidence": "C2",                       # 条件实证：过 FINAL 证据闸门+独立复现（§10.2②）
            "impact": p["impact"],
            "exploitation_status": "verified",
            "auth_context": "",
            "reproducible_steps": p["steps"],
            "evidence_refs": ["%s@%s" % (e, stem) for e in p["evidence"]],
            "location": p["location"] or target,
            "dedup_key_proposed": "%s-%s+vulnclaw" % (p["fid"], p["vtype"]),
            "network_position": net_pos,
            "preconditions": ["目标 %s 可达（VulnClaw solve 只读评估）" % target],
            "expected_matcher": {},
        })

    # ① findings[] 规则层候选只当线索队列（§10.2④a：证据串=模板碎片，甚至与否定结论矛盾）
    for fd in d.get("findings") or []:
        facts.append({"kind": "vuln-clue",
                      "target": _clip(fd.get("target") or target, 80),
                      "detail": _clip("findings[] 规则层候选（%s/%s/verified=%s）降权为线索队列——"
                                      "证据为模板碎片不可采信（vulnclaw-live-trial §10.2④a），"
                                      "升级须人证复核"
                                      % (fd.get("title", "?"), fd.get("severity", "?"),
                                         fd.get("verified")), 240),
                      "confidence": 0.5})
    # 否定结果（§10.2②：往往更值钱）+未测项+合规+claims——全部走 facts（info）
    for n in negs:
        facts.append({"kind": "info", "target": target,
                      "detail": _clip("否定结果（已测不可重现）：" + n, 220), "confidence": 0.85})
    for u in untes:
        facts.append({"kind": "info", "target": target,
                      "detail": _clip("未测项（范围外诚实披露）：" + u, 180), "confidence": 0.7})
    if compliance:
        facts.append({"kind": "info", "target": target,
                      "detail": "范围合规性：" + compliance, "confidence": 0.9})
    for c in claims:
        if isinstance(c, dict):
            facts.append({"kind": "info", "target": target,
                          "detail": _clip("verified_claim %s：%s（证据=%s）"
                                          % (c.get("id", "?"), c.get("claim", ""),
                                             ",".join(c.get("evidence_ids") or [])), 240),
                          "confidence": 0.9})
    if final_line:
        facts.append({"kind": "info", "target": target,
                      "detail": _clip("FINAL 完成断言：" + final_line, 220), "confidence": 0.9})
    tc = d.get("task_constraints") or {}
    facts.append({"kind": "info", "target": target,
                  "detail": "task_constraints: allowed_ports=%s blocked_ports=%s "
                            "allowed_hosts=%s strict=%s violations=%d"
                            % (tc.get("allowed_ports"), tc.get("blocked_ports"),
                               tc.get("allowed_hosts"), tc.get("strict_mode"),
                               len(d.get("constraint_violations") or [])),
                  "confidence": 1.0})
    for v in d.get("constraint_violations") or []:
        facts.append({"kind": "info", "target": target,
                      "detail": _clip("constraint_violation: " + str(v), 200),
                      "confidence": 1.0})
    facts.append({"kind": "info", "target": target,
                  "detail": _clip("solve 概况: completed=%s tool_calls=%d evidence=%d "
                                  "findings候选=%d steps=%d reason=%s"
                                  % (asx.get("completed"),
                                     len(asx.get("tool_calls") or []),
                                     len(asx.get("evidence") or []),
                                     len(d.get("findings") or []),
                                     len(asx.get("steps") or []),
                                     asx.get("complete_reason", "")), 260),
                  "confidence": 1.0})

    assets.append({"type": "app", "value": target, "meta": "source=vulnclaw-solve"})
    seen = set()
    for p in parsed:                                  # 端点图谱→endpoint 资产（§9.4 情报层）
        loc = p["location"]
        if loc and loc.startswith("/") and loc not in seen and len(seen) < 20:
            seen.add(loc)
            assets.append({"type": "endpoint", "value": target.rstrip("/") + loc,
                           "meta": "final_answer " + p["fid"]})
    status = "done" if (findings or claims) else "no-findings"
    return {"intent_id": intent_id, "engine": "vulnclaw", "status": status,
            "facts": facts, "findings": findings, "assets": assets,
            "edges": [], "creds": [], "operations_log": "operations.log"}


def _blocked(intent_id):
    return {"intent_id": intent_id, "engine": "vulnclaw", "status": "blocked",
            "facts": [], "findings": [], "assets": [], "edges": [], "creds": [],
            "operations_log": "operations.log"}


def _dump(sub, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sub, f, ensure_ascii=False, indent=1, sort_keys=True)


def main(argv):
    args = parse_argv(argv)
    for k in ("--intent-id", "--out-dir"):
        if not args.get(k):
            sys.stderr.write(USAGE)
            return 2
    session, run_mode = args.get("--session", ""), "--run" in args
    if not session and not run_mode:
        sys.stderr.write(USAGE)
        return 2
    if run_mode and not (args.get("--target") and args.get("--goal")):
        sys.stderr.write(USAGE)
        return 2
    out = args["--out-dir"]
    os.makedirs(out, exist_ok=True)
    log = open(os.path.join(out, "operations.log"), "w", encoding="utf-8", newline="\n")
    markers, p02, events = [], False, args.get("--events-file", "")

    if run_mode:
        goal, target = args["--goal"], args["--target"]
        hits = blacklist_hits(goal)                    # ② 预筛先于一切（fail-closed）
        if hits:
            log.write("blacklist: HIT " + "; ".join("%s:%s" % h for h in hits) + "\n")
            log.write("blacklist: 预筛拦截——goal 命中副作用黑名单（删库/关机/外发），"
                      "拒绝启动，不走 prompt 措辞自觉（§10.2④b）\n")
            _dump(_blocked(args["--intent-id"]), os.path.join(out, "submission.json"))
            print("OK submission.json status=blocked reason=side-effect-blacklist")
            return 0
        log.write("blacklist: pass（goal 未命中副作用黑名单）\n")
        cons = build_constraints(target)
        with open(os.path.join(out, "task-constraints.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump(cons, f, ensure_ascii=False, indent=1, sort_keys=True)
        log.write("constraints: task-constraints.json 落盘 blocked_actions=%s "
                  "blocked_ports=%s strict=true（结构化通道，§6.3/§10.2④b）\n"
                  % (",".join(BLOCKED_ACTIONS), ",".join(str(p) for p in FORBIDDEN_PORTS)))
        binp = args.get("--vulnclaw") or shutil.which("vulnclaw")
        if not binp or not os.path.isfile(binp):
            _dump(_blocked(args["--intent-id"]), os.path.join(out, "submission.json"))
            log.write("env: vulnclaw 可执行缺失（运行时绝不自动安装——契约 10 §4）\n")
            print("OK submission.json status=blocked reason=vulnclaw-missing")
            return 0
        _host, port = _split_target(target)
        if "仅允许测试" not in goal:
            goal += "；仅允许测试 %d 端口，禁止测试 %s 端口；禁止删库/关机/外发等破坏性副作用" \
                % (port or 0, ",".join(str(p) for p in FORBIDDEN_PORTS))
            log.write("goal: 增补固定句式 scope+副作用禁令（§9.2 教训：句式不命中=不受硬执法）\n")
        cmd = [binp, "solve", target, "--goal", goal, "--stream",
               "--run-name", args["--intent-id"]]
        log.write("run: vulnclaw solve %s --stream --run-name %s\n" % (target, args["--intent-id"]))
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                               encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            _dump(_blocked(args["--intent-id"]), os.path.join(out, "submission.json"))
            print("OK submission.json status=blocked reason=run-timeout")
            return 0
        stream_path = os.path.join(out, "stream.ndjson")
        with open(stream_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(r.stdout or "")
        log.write("run: exit=%d\n" % r.returncode)
        err = r.stderr or ""
        p02 = "not subscriptable" in err or ("TypeError" in err and "verified_claims" in err)
        if r.returncode != 0 and not p02:
            _dump(_blocked(args["--intent-id"]), os.path.join(out, "submission.json"))
            print("OK submission.json status=blocked reason=run-exit-%d" % r.returncode)
            return 0
        if p02:
            log.write("P0#2 崩溃捕获: exit=%d stderr 含 findings 组装崩溃签名——"
                      "编排层已记 run_complete，改走 session.json 手动归一（§9.6/§10.4①）\n"
                      % r.returncode)
        events = stream_path
        if not session:
            sdir = os.path.join(args.get("--config-dir") or os.path.expanduser("~/.vulnclaw"),
                                "sessions")
            cands = ([os.path.join(sdir, f) for f in sorted(os.listdir(sdir))
                      if f.endswith(".json") and not f.startswith("subagent_")]
                     if os.path.isdir(sdir) else [])
            if not cands:
                _dump(_blocked(args["--intent-id"]), os.path.join(out, "submission.json"))
                log.write("env: sessions/ 无会话文件（P0#2 绕过路径需要 session.json）\n")
                print("OK submission.json status=blocked reason=session-not-found")
                return 0
            session = max(cands, key=os.path.getmtime)
            log.write("session: 取最新 %s\n" % os.path.basename(session))
        if p02:                                        # ④ 手动 report 规避（§9.6 实测路径）
            try:
                rr = subprocess.run([binp, "report", session], capture_output=True,
                                    text=True, timeout=600, encoding="utf-8", errors="replace")
                log.write("manual-report: exit=%d\n" % rr.returncode)
            except (subprocess.SubprocessError, OSError) as e:
                log.write("manual-report: 失败（不阻断归一）%s\n" % e)

    if not p02 and events and not _complete_present(events):
        log.write("P0#2 绕过: stream 无 complete 事件（CLI 收尾组装 findings 崩溃，"
                  "cli/main.py:1609）——改走 session.json 手动归一，"
                  "等价手动 vulnclaw report 规避路径（§9.6/§10.4①）\n")
    if p02 or (events and not _complete_present(events)):
        markers.append("p02-bypass=1")

    sub = normalize(session, args["--intent-id"], log)
    if args.get("--usage-file"):                      # ③ 网关侧 usage 外挂回填
        agg = load_usage(args["--usage-file"])
        art = os.path.join(out, "artifacts")
        os.makedirs(art, exist_ok=True)
        shutil.copyfile(args["--usage-file"], os.path.join(art, "usage-backfill.json"))
        sub["facts"].append({"kind": "info", "target": args["--intent-id"],
                             "detail": "usage-backfill(网关侧) token=%d requests=%d "
                                       "dollars=%.4f 记录=%d——引擎内建 usage 计量不可信不采信"
                                       "（vulnclaw-live-trial §9.5/§10.4④）"
                                       % (agg["total_tokens"], agg["requests"],
                                          agg["dollars"], agg["records"]),
                             "confidence": 1.0})
        log.write("usage-backfill: 网关侧 token=%d requests=%d dollars=%.4f source=%s\n"
                  % (agg["total_tokens"], agg["requests"], agg["dollars"], args["--usage-file"]))
    else:
        sub["facts"].append({"kind": "info", "target": args["--intent-id"],
                             "detail": "usage 外挂缺位：网关侧 usage 未提供；引擎内建计量"
                                       "不可信不采信（成本待网关侧对账）", "confidence": 1.0})
        log.write("usage: 未提供外挂——引擎内建计量不可信，不采信\n")
    _dump(sub, os.path.join(out, "submission.json"))
    log.write("normalize: findings=%d facts=%d assets=%d\n"
              % (len(sub["findings"]), len(sub["facts"]), len(sub["assets"])))
    print("OK submission.json status=%s findings=%d facts=%d assets=%d%s"
          % (sub["status"], len(sub["findings"]), len(sub["facts"]), len(sub["assets"]),
             (" " + " ".join(markers)) if markers else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
