# -*- coding: utf-8 -*-
"""外部执行后端·归一入账（功能24a §3 记录行归一——本舰心脏）。

外部肌肉的产出不是天然可信：归一层把外部回传的 facts/findings 经**既有
写入通道**（registry.lookup → goal 写锁 → 既有校验执法链）落账——
哨兵前置门/验证官复放/GT 棘轮对外部产出**零豁免**（与 Multica 的根本
差异：它无质量门层）。规划者舰 R-PLN-3 同款纪律：不私铸 TSV 行。

流水：
1. result.output 解析（确定性去栅栏，judge_client 同款剥离律——绝不
   补全截断）；非 JSON/非对象=不可归一 → 原始流落 backends/<task>.raw
   .jsonl + timeline backend-unnormalizable 事件（人工通道，可回放）。
2. findings 先铸证据（add-evidence——findings 须 evidence_ids 闭合=
   铁律 4；artifact 落 backends/<task>/ 命名空间），再 add-finding——
   哨兵 reject=拒收留痕；downgrade-to-fact=降级落 facts（账本自己的
   降级路径，非旁门）。
3. 枚举校验前置（confidence/impact/exploitation_status/scope_check/
   fact.kind）——不合账本枚举=拒收记 rejected，不硬编不猜。
4. usage 四 token 维 → budget-log 入 budget.tsv（requests=1/次任务；
   dollars 维只在 goal 开 dollar_budget 才入账——ADR-P4⑥ 既有执法，
   旁路即被既有链拒）。

失败语义：单条拒收不废整批（逐条留痕）；预算记账失败不影响归一判定
（记账 fail-open，预算执法不被旁路——BudgetMeter 同律）。
"""
import contextlib
import io
import json
import os

from .base import Usage

FINDING_REQUIRED = ("title", "confidence", "impact", "exploitation_status",
                    "scope_check", "description_brief", "reproducible_steps",
                    "affected_asset_id", "evidence")
FINDING_CONFIDENCE = {"C1", "C2", "C3", "\u2796\U0001f6d1"}
FINDING_IMPACT = {"\u9ad8", "\u4e2d", "\u4f4e"}
FINDING_EXPLOITATION = {"verified", "suspected", "ruled_out"}
FINDING_SCOPE = {"in_scope", "boundary-verified"}
FACT_KINDS = {"port", "service", "http", "info", "vuln-clue", "authz"}


def _strip_fence(text):
    """确定性去栅栏（judge_client 同律）：成对完整才剥，绝不补全。"""
    t = (text or "").strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            body = t[nl + 1:].rstrip()
            if body.endswith("```"):
                return body[:-3].strip()
    return t


def parse_output(result):
    """result.output → payload dict|None（不可归一=None，不外抛）。"""
    if not result.is_ok():
        return None
    try:
        doc = json.loads(_strip_fence(result.output))
    except ValueError:
        return None
    return doc if isinstance(doc, dict) else None


def _run(goal_dir, cmd, args):
    """既有写入通道（goal 写锁+执法链），stdout 捕获；返回 (rc, out, id)。"""
    import ledger.registry as registry
    h = registry.lookup(cmd)
    if h is None:
        return 2, "未知命令: " + cmd, ""
    rest = ["--%s=%s" % (k, v) for k, v in args.items()]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            rc = h(goal_dir, rest)
        except Exception as e:                  # noqa: BLE001
            return 1, "FAIL %s" % e, ""
    out = buf.getvalue()
    rid = ""
    for ln in out.splitlines():
        parts = ln.split("\t")
        if len(parts) >= 3 and parts[0] == "OK":
            rid = parts[1]
            break
    return rc, out, rid


def _evidence_list(finding):
    ev = finding.get("evidence")
    if isinstance(ev, dict):
        return [ev]
    if isinstance(ev, list):
        return [e for e in ev if isinstance(e, dict)]
    return []


def _add_evidence(goal_dir, task_id, idx, ev, ts):
    excerpt = str(ev.get("excerpt", "") or "")
    repro = str(ev.get("repro", "") or ("external:%s" % task_id))
    return _run(goal_dir, "add-evidence", {
        "title": "backend-evidence %s #%d" % (task_id, idx),
        "source-type": "capture",
        "observed-at": ts,
        "network-position": "internet",
        "repro-command": repro,
        "repro-kind": "single",
        "artifact": "backends/%s/ev-%d.txt" % (task_id, idx),
        "raw-excerpt": excerpt,
        "timestamp": ts,
    })


def _validate_finding(f):
    """枚举/必填前置校验 → 拒收理由（空串=过）。"""
    for k in FINDING_REQUIRED:
        if not f.get(k):
            return "缺必填字段: %s" % k
    if f["confidence"] not in FINDING_CONFIDENCE:
        return "confidence 不在枚举 {C1,C2,C3,%s}" % (
            ",".join(sorted(FINDING_CONFIDENCE)))
    if f["impact"] not in FINDING_IMPACT:
        return "impact 不在枚举 {高,中,低}"
    if f["exploitation_status"] not in FINDING_EXPLOITATION:
        return "exploitation_status 不在枚举 {verified,suspected,ruled_out}"
    if f["scope_check"] not in FINDING_SCOPE:
        return "scope_check 不在枚举 {in_scope,boundary-verified}"
    if not _evidence_list(f):
        return "evidence 空=REJECT（铁律 4：finding 须证据支撑）"
    return ""


def _ingest_finding(goal_dir, f, task_id, intent_id, ts, report):
    why = _validate_finding(f)
    if why:
        report["rejected"].append({"kind": "finding", "title":
                                   f.get("title", ""), "why": why})
        return
    ev_ids = []
    for i, ev in enumerate(_evidence_list(f), start=1):
        rc, out, rid = _add_evidence(goal_dir, task_id, i, ev, ts)
        if rc != 0 or not rid:
            report["rejected"].append({
                "kind": "finding", "title": f.get("title", ""),
                "why": "证据铸行失败: " + out.strip()[:200]})
            return
        ev_ids.append(rid)
        report["evidence"].append(rid)
    args = {
        "intent-id": intent_id,
        "title": str(f["title"]),
        "confidence": str(f["confidence"]),
        "impact": str(f["impact"]),
        "exploitation-status": str(f["exploitation_status"]),
        "scope-check": str(f["scope_check"]),
        "description-brief": str(f["description_brief"]),
        "reproducible-steps": str(f["reproducible_steps"]),
        "affected-asset-id": str(f["affected_asset_id"]),
        "evidence-ids": ";".join(ev_ids),
        "timestamp": ts,
    }
    if f.get("vuln_ref"):
        args["vuln-ref"] = str(f["vuln_ref"])
    rc, out, rid = _run(goal_dir, "add-finding", args)
    if rc != 0:
        # 既有执法链拒（哨兵 reject/引用闭合/dedup…）——留痕不硬编
        report["rejected"].append({"kind": "finding",
                                   "title": f.get("title", ""),
                                   "why": out.strip()[:300]})
        return
    if rid.startswith("F-"):
        # 哨兵 downgrade-to-fact：外部产出照走账本降级路径（零豁免证据位）
        report["downgraded"].append({"title": f.get("title", ""),
                                     "fact_id": rid})
        return
    report["findings"].append(rid)


def _ingest_fact(goal_dir, f, intent_id, ts, report):
    if f.get("kind") not in FACT_KINDS:
        report["rejected"].append({"kind": "fact",
                                   "why": "kind 不在枚举 %s"
                                   % sorted(FACT_KINDS)})
        return
    try:
        cf = float(f.get("confidence"))
        assert 0.0 <= cf <= 1.0
    except (TypeError, ValueError, AssertionError):
        report["rejected"].append({"kind": "fact",
                                   "why": "confidence 不在 [0,1]"})
        return
    rc, out, rid = _run(goal_dir, "add-fact", {
        "intent-id": intent_id,
        "kind": str(f["kind"]),
        "target": str(f.get("target", "")),
        "detail": str(f.get("detail", "")),
        "confidence": str(f.get("confidence")),
        "timestamp": ts,
    })
    if rc != 0 or not rid:
        report["rejected"].append({"kind": "fact",
                                   "why": out.strip()[:300]})
        return
    report["facts"].append(rid)


def _budget_log(goal_dir, backend_name, task_id, usage, intent_id, ts):
    """usage → budget.tsv（四维全计；dollars 维按 goal 开关门）。"""
    from ledger.core import Session
    dollars = "0"
    try:
        grows = Session(goal_dir).rows("goals.tsv")
        if grows and grows[-1][12] not in ("", "0"):
            dollars = "%.10f" % usage.dollars()
    except Exception:                            # noqa: BLE001
        dollars = "0"
    note = "backend=%s model=%s task=%s" % (backend_name, usage.model,
                                            task_id)
    rc, _out, _rid = _run(goal_dir, "budget-log", {
        "token-delta": str(usage.total_tokens()),
        "requests-delta": "1",
        "hours-delta": "0",
        "dollars-delta": dollars,
        "scope": intent_id or "goal",
        "note": note,
        "timestamp": ts,
    })
    return rc == 0


def _raw_channel(goal_dir, backend_name, task_id, result, frames, ts, why):
    """不可归一：原始流落盘+timeline 事件（人工通道，不硬编）。"""
    from ledger.timeline import append_tl_locked
    d = os.path.join(goal_dir, "backends")
    try:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "%s.raw.jsonl" % task_id)
        with open(path, "w", encoding="utf-8") as f:
            for fr in frames:
                f.write(json.dumps(fr, ensure_ascii=False,
                                   sort_keys=True) + "\n")
            f.write(json.dumps({"type": "result", "status": result.status,
                                "output": result.output,
                                "error": result.error},
                               ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        path = ""
    append_tl_locked(
        goal_dir, ts,
        "backend-unnormalizable backend=%s task=%s reason=%s raw=%s"
        % (backend_name, task_id, why[:120], path or "-"),
        actor="backend:" + backend_name, phase="P3")
    return path


def ingest_result(goal_dir, backend_name, task_id, result, frames, ts,
                  intent_id=""):
    """归一入账主入口 → 报告 dict（facts/findings/evidence/downgraded/
    rejected/budget_logged/normalizable/raw_path）。"""
    report = {"normalizable": False, "facts": [], "findings": [],
              "evidence": [], "downgraded": [], "rejected": [],
              "budget_logged": False, "raw_path": ""}
    usage = result.usage if isinstance(result.usage, Usage) else Usage()
    payload = parse_output(result)
    if payload is None:
        why = ("后端非 ok 终态" if not result.is_ok()
               else "output 非 JSON 对象")
        if frames or result.output or not result.is_ok():
            report["raw_path"] = _raw_channel(
                goal_dir, backend_name, task_id, result, frames, ts, why)
    else:
        report["normalizable"] = True
        for f in (payload.get("findings") or []):
            if isinstance(f, dict):
                _ingest_finding(goal_dir, f, task_id, intent_id, ts, report)
        for f in (payload.get("facts") or []):
            if isinstance(f, dict):
                _ingest_fact(goal_dir, f, intent_id, ts, report)
    report["budget_logged"] = _budget_log(
        goal_dir, backend_name, task_id, usage, intent_id, ts)
    return report
