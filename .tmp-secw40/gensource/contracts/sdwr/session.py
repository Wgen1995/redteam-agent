import csv
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_CONTRACTS = str(Path(__file__).resolve().parent.parent)
if _CONTRACTS not in sys.path:
    sys.path.insert(0, _CONTRACTS)

from sdwr.rewrite import apply_rewrite
from sdwr.worklist import _band, order_cards, wake_blocked, HIGH_RISK_BANDS

SHARD_VERDICT = {
    "candidate": "candidate",
    "disproved": "disproved",
    "blocked": "blocked",
    "unconfirmed": "blocked",
    "not_applicable": "not_applicable",
}

WL_FIELDS = [
    "card_id", "basis_id", "direction", "sink_type", "module",
    "band", "status", "depends_on", "source", "must_through",
    "entry_types", "component", "has_bypass", "reason",
    "evidence_summary", "evidence_refs",
]

# candidates.tsv 的 16 列顺序权威——必须与 gate-1.py 的 CAND_COLS 逐字一致，
# 否则 gate[schema 全等] FAIL。见 contracts/data-structures/candidate-finding.md。
CAND_FIELDS = [
    "candidate_id", "location", "sink_type", "severity_hypothesis_initial",
    "root_cause_group_id", "lifecycle_state", "verdict", "cluster_ref",
    "verification_record_ref", "report_record_ref", "created_at",
    "discovery_source", "path", "start_line", "end_line",
    "discovery_reasoning_note",
]
FACT_FIELDS = [
    "fact_id", "type", "source_role", "scope", "sink_type", "function", "component",
    "src", "dst", "sink_id", "blocks", "evidence", "confirmed",
    "confirmed_by", "timestamp",
]
FACT_SOURCE_ROLES = {"summarizer", "analyzer", "verifier"}
FACT_TYPES = {
    "uncontrolled", "intended", "kills", "propagates",
    "no_edge", "dead", "flow", "requires_config", "must_through",
}


def validate_fact_row(row):
    """污染1防御：格式校验，不判语义。返回 None（合法）或错误原因字符串。"""
    if not row.get("fact_id"):
        return "missing fact_id"
    t = row.get("type")
    if t not in FACT_TYPES:
        return "invalid type: %r" % t
    confirmed_raw = (row.get("confirmed") or "").strip().lower()
    if confirmed_raw not in ("true", "false", ""):
        return "invalid confirmed: %r (must be true/false)" % row.get("confirmed")
    evidence = (row.get("evidence") or "").strip()
    if confirmed_raw == "true" and not evidence:
        return "confirmed=true requires non-empty evidence"
    if evidence and ":" not in evidence:
        return "evidence must be file:line format: %r" % evidence
    source_role = (row.get("source_role") or "").strip().lower()
    if source_role and source_role not in FACT_SOURCE_ROLES:
        return "invalid source_role: %r (must be summarizer/analyzer/verifier or empty)" % row.get("source_role")
    return None


def split_valid_facts(rows):
    """按行校验，返回 (合法行列表, 拒绝行列表[(row, reason)])。"""
    valid, rejected = [], []
    for row in rows:
        reason = validate_fact_row(row)
        if reason:
            rejected.append((row, reason))
        else:
            valid.append(row)
    return valid, rejected


def _read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return rows


def _write_tsv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def _module_of(location):
    rel = (location or "").split(":", 1)[0]
    parts = rel.replace("\\", "/").split("/")
    return parts[0] if parts and parts[0] else ""


def _component_of(location):
    """类级剪枝的 component 必须是"类"这个粒度（Summarizer 角色本名"类级事实编写者"），
    不是顶层目录。若按顶层目录派生，对源码全部挂在单一根目录下的项目（如 Tomcat 的
    java/），所有文件的 component 都会退化成同一个值（如"java"），导致 Summarizer 写的
    intended fact（component 为真实类名，如"StandardSession"）永远匹配不上任何卡，
    intended 级联完全失效。用文件 basename 去掉扩展名近似类名：单文件单主类语言
    （Java/Go/大多数 Python 模块）下是合理近似；多类文件/非OOP语言此字段仅供参考，
    Confirmer/Analyzer 核验时仍以 evidence file:line 为准，不影响正确性。"""
    rel = (location or "").split(":", 1)[0]
    fname = rel.replace("\\", "/").rsplit("/", 1)[-1]
    return fname.rsplit(".", 1)[0] if "." in fname else fname


def _ledger_status(terminal):
    if terminal in ("", "未检查", None):
        return "unchecked"
    return terminal


def build_worklist(session_dir):
    session = Path(session_dir)
    sinks = _read_tsv(session / "sink_inventory.tsv")
    ledger = _read_tsv(session / "check_point_ledger.tsv")
    if not sinks or not ledger:
        raise SystemExit("FATAL: need sink_inventory.tsv and check_point_ledger.tsv")
    sink_type = {}
    sink_loc = {}
    for r in sinks[1:]:
        if len(r) >= 3:
            sink_type[r[0]] = r[2]
            sink_loc[r[0]] = r[1]
    src_type = {}
    src_loc = {}
    srcp = session / "source_inventory.tsv"
    if srcp.exists():
        for r in _read_tsv(srcp)[1:]:
            if len(r) >= 3:
                src_type[r[0]] = r[2]
                src_loc[r[0]] = r[1]
    # file_call_targets: file -> 该文件调用/引入的符号集合（供 depends_on 唤醒用）
    file_call_targets = {}
    edges_path = session / "call_edges.tsv"
    if edges_path.exists():
        edge_rows = _read_tsv(edges_path)
        if len(edge_rows) > 1:
            for r in edge_rows[1:]:
                if len(r) >= 2:
                    src_file, target = r[0], r[1]
                    file_call_targets.setdefault(src_file, set()).add(target)
    # also from source_inventory: entry_type per source file
    src_file_entry = {}
    for sid, et in src_type.items():
        loc = src_loc.get(sid, "")
        if ":" in loc:
            f = loc.split(":", 1)[0]
            src_file_entry.setdefault(f, set()).add(et)
    cards = []
    for r in ledger[1:]:
        if len(r) < 6:
            continue
        basis, direction, _mech, cpid, _cands, terminal = r[0], r[1], r[2], r[3], r[4], r[5]
        if direction == "forward":
            st = "ENTRY-" + (src_type.get(basis) or "unknown")
            loc = src_loc.get(basis, "")
        elif direction == "terminal":
            st = "FILE"
            loc = basis
        else:
            st = sink_type.get(basis, "")
            loc = sink_loc.get(basis, "")
        mod = _module_of(loc)
        # entry_types: for backward cards, find entry types in same file
        ets = ""
        if direction == "backward" and ":" in loc:
            sink_file = loc.split(":", 1)[0]
            types = src_file_entry.get(sink_file, set())
            if types:
                ets = ";".join(sorted(types))
        # depends_on：该卡所在文件调用/引入的符号集合，供 wake_blocked 用新事实符号唤醒
        dep = ""
        card_file = loc.split(":", 1)[0] if ":" in loc else loc
        targets = file_call_targets.get(card_file, set())
        if targets:
            dep = ";".join(sorted(targets))
        cards.append({
            "card_id": cpid,
            "basis_id": basis,
            "direction": direction,
            "sink_type": st,
            "module": mod,
            "band": str(_band(st)),
            "status": _ledger_status(terminal),
            "depends_on": dep,
            "source": "inventory",
            "must_through": "",
            "entry_types": ets,
            "component": _component_of(loc),
            "has_bypass": "",
            "reason": "",
        })
    wl_path = session / "worklist.tsv"
    if wl_path.exists():
        prev = {}
        with wl_path.open(encoding="utf-8", newline="") as f:
            for old in csv.DictReader(f, delimiter="\t"):
                prev[old.get("card_id", "")] = old
        for card in cards:
            old = prev.get(card["card_id"])
            if old and old.get("status") not in ("", "unchecked", None):
                card["status"] = old["status"]
            if old and old.get("must_through"):
                card["must_through"] = old["must_through"]
            if old and old.get("entry_types"):
                card["entry_types"] = old["entry_types"]
            if old and old.get("has_bypass"):
                card["has_bypass"] = old["has_bypass"]
            if old and old.get("reason"):
                card["reason"] = old["reason"]
    _write_tsv(wl_path, WL_FIELDS, cards)
    _ensure_pruning_ledger_exists(session)
    return len(cards)


PRUNING_LEDGER_FIELDS = ["operator", "criterion", "scope", "evidence", "judged_by", "timestamp", "a2_verified"]


def _ensure_pruning_ledger_exists(session):
    """兜底创建 pruning_ledger.tsv 表头：gate「剪枝判据落盘」只要求文件存在（空表头
    也算过）。在 build_worklist 时机械创建表头，保证文件至少存在；真实的剪枝判据行由
    Summarizer（class-pruner-prompt.md）追加，小项目/无可剪类别时表头单独存在也合法。"""
    pl_path = Path(session) / "pruning_ledger.tsv"
    if not pl_path.exists():
        _write_tsv(pl_path, PRUNING_LEDGER_FIELDS, [])


TEMPLATED_EVIDENCE_THRESHOLD = 5


def detect_templated_evidence(session_dir):
    """检测模板化/伪造证据：真实 Tomcat 审计验证过，主代理绕开
    Analyzer 子代理、自己写脚本给 7835+ 张卡编造同一段模板文本当"五段证据"（如
    "source=safe_at_class_level|propagation=confirmed_by_Confirmer|..."，只有 sink_type
    在变，其余逐字相同）——每行的 file:line 引用是真的（来自 sink_inventory），所以
    gate「证据唯一性」（同一引用用超过50次才报警）完全抓不住这种"位置各异但正文模板化"
    的批量造假。这里改用不同判据：同一段 five_segment_evidence 原文在不同 sink_id 间
    重复次数超阈值即视为可疑（真实的逐 sink 独立分析，即使结论相同，具体证据文本也应
    有差异——不同文件/行号/变量名/上下文）。返回可疑证据文本列表及各自重复次数，供
    drive 在输出里打印提醒，不阻断（可能有极少数场景合理重复，交给人工/A2复核判断）。"""
    session = Path(session_dir)
    seen = {}
    for shard in session.glob("batches/**/*.tsv"):
        if shard.name.endswith("-audit.tsv") or shard.name.endswith("-flow.tsv"):
            continue
        try:
            with shard.open(encoding="utf-8", newline="") as f:
                for rec in csv.DictReader(f, delimiter="\t"):
                    ev = (rec.get("five_segment_evidence") or "").strip()
                    sid = rec.get("sink_id") or rec.get("basis_id") or ""
                    if not ev or not sid:
                        continue
                    seen.setdefault(ev, set()).add(sid)
        except (OSError, csv.Error):
            continue
    return sorted(
        ((ev, len(sids)) for ev, sids in seen.items() if len(sids) > TEMPLATED_EVIDENCE_THRESHOLD),
        key=lambda x: -x[1],
    )


def ingest_shards(session_dir):
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        build_worklist(session_dir)
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    by_basis = {}
    for row in rows:
        by_basis.setdefault(row.get("basis_id", ""), []).append(row)
    n = 0
    for shard in session.glob("batches/**/WU-*.tsv"):
        if shard.name.endswith("-audit.tsv") or shard.name.endswith("-flow.tsv"):
            continue
        wu_id = shard.stem
        with shard.open(encoding="utf-8", newline="") as f:
            for rec in csv.DictReader(f, delimiter="\t"):
                sid = rec.get("sink_id") or rec.get("basis_id")
                mapped = SHARD_VERDICT.get((rec.get("verdict") or "").strip())
                bypass = str(rec.get("has_bypass") or "").strip().lower() == "true"
                if not sid or not mapped:
                    continue
                for row in by_basis.get(sid, []):
                    if bypass:
                        row["has_bypass"] = "true"
                    # 证据字段（evidence_summary/evidence_refs）是纯描述性信息，不影响
                    # 判定逻辑，无条件刷新——目的是修复一批"改造前已经 ingest 过、状态
                    # 已经不是未检查"的历史卡片：此前它们的 evidence 字段永远是空的，
                    # 因为下面的写入原本被限制在"仅未检查时才写"的分支里，真实 dvpwa
                    # 冒烟跑就撞上了这个问题——22 个 candidate 里除了本次改动后新落的
                    # 2 个，其余 20 个全部拿不到证据文本，只能显示 basis_id 兜底。
                    if not row.get("evidence_summary"):
                        row["evidence_summary"] = rec.get("five_segment_evidence", "")
                    if not row.get("evidence_refs"):
                        row["evidence_refs"] = rec.get("evidence_refs", "")
                    if row.get("status") in ("", "unchecked", None):
                        row["status"] = mapped
                        row["reason"] = "shard:%s" % wu_id
                        n += 1
    _write_tsv(wl_path, WL_FIELDS, rows)
    return n


def ingest_summarizer_shards(session_dir):
    """归并 Summarizer 各自的分片文件到 facts.tsv / pruning_ledger.tsv。

    真实审计中发现：多个 Summarizer 子代理各自直接对同一份共享 facts.tsv/pruning_ledger.tsv
    做"读全文件→追加→整写回"，并发/连续执行时会互相覆盖对方刚写的内容（Tomcat 实测：5 个
    Summarizer 报告共写 129 条事实，最终落盘只剩 55-90 条，丢了 30%-57%）。修法是让每个
    Summarizer 只写自己的分片文件（不碰共享文件），由 drive 统一归并——与 Analyzer 的
    `batches/**/WU-*.tsv` 分片模式同构，天然避免竞态。

    分片命名：`{session_dir}/summarizer_shards/{judged_by}-facts.tsv` 与
    `{session_dir}/summarizer_shards/{judged_by}-pruning.tsv`（judged_by 如 SUM-1，与
    pruning_ledger 的 judged_by 列对应，便于溯源）。

    幂等：facts 按 fact_id 去重（已在 facts.tsv 里的不重复追加），pruning_ledger 按整行内容
    去重——重复跑 drive 不会重复归并。
    """
    session = Path(session_dir)
    shard_dir = session / "summarizer_shards"
    if not shard_dir.exists():
        return 0

    fp = session / "facts.tsv"
    existing_facts = []
    existing_fact_ids = set()
    if fp.exists():
        with fp.open(encoding="utf-8", newline="") as f:
            existing_facts = list(csv.DictReader(f, delimiter="\t"))
        existing_fact_ids = {r.get("fact_id") for r in existing_facts}

    plp = session / "pruning_ledger.tsv"
    existing_pruning = []
    existing_pruning_keys = set()
    if plp.exists():
        with plp.open(encoding="utf-8", newline="") as f:
            existing_pruning = list(csv.DictReader(f, delimiter="\t"))
        existing_pruning_keys = {tuple(r.get(k, "") for k in PRUNING_LEDGER_FIELDS[:5]) for r in existing_pruning}

    added_facts = 0
    for shard in sorted(shard_dir.glob("*-facts.tsv")):
        with shard.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                fid = row.get("fact_id")
                if not fid or fid in existing_fact_ids:
                    continue
                existing_facts.append(row)
                existing_fact_ids.add(fid)
                added_facts += 1
    if added_facts:
        _write_tsv(fp, FACT_FIELDS, existing_facts)

    added_pruning = 0
    for shard in sorted(shard_dir.glob("*-pruning.tsv")):
        with shard.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                key = tuple(row.get(k, "") for k in PRUNING_LEDGER_FIELDS[:5])
                if key in existing_pruning_keys:
                    continue
                existing_pruning.append(row)
                existing_pruning_keys.add(key)
                added_pruning += 1
    if added_pruning:
        _write_tsv(plp, PRUNING_LEDGER_FIELDS, existing_pruning)

    return added_facts


def ingest_confirmer_shards(session_dir):
    """归并 Confirmer 各自的确认决定分片到 facts.tsv。

    真实审计中发现：多个 Confirmer 子代理都被要求"覆盖 facts.tsv（只改 confirmed/
    confirmed_by 列）"——这是同一种"读全文件→改→整写回"共享文件竞态，与 Summarizer
    的问题同源，实测导致 facts.tsv 出现同一 fact_id 的重复行。

    修法同构：Confirmer 只写自己的决定分片 `confirmer_shards/{confirmed_by}-decisions.tsv`
    （表头 `fact_id\tconfirmed\tconfirmed_by\treason`），不碰共享 facts.tsv；drive 统一按
    fact_id 把决定应用到 facts.tsv 对应行（只更新 confirmed/confirmed_by 两列，不新增行，
    不产生重复）。幂等：重复应用同一决定分片结果不变。
    """
    session = Path(session_dir)
    shard_dir = session / "confirmer_shards"
    if not shard_dir.exists():
        return 0
    fp = session / "facts.tsv"
    if not fp.exists():
        return 0
    with fp.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    by_id = {}
    for r in rows:
        by_id.setdefault(r.get("fact_id"), []).append(r)

    applied = 0
    for shard in sorted(shard_dir.glob("*-decisions.tsv")):
        with shard.open(encoding="utf-8", newline="") as f:
            for dec in csv.DictReader(f, delimiter="\t"):
                fid = (dec.get("fact_id") or "").strip()
                if not fid or fid not in by_id:
                    continue
                confirmed = (dec.get("confirmed") or "").strip().lower()
                if confirmed not in ("true", "false"):
                    continue
                confirmed_by = dec.get("confirmed_by") or ""
                reason = dec.get("reason") or ""
                cb = confirmed_by if confirmed == "true" or not reason else "%s:%s" % (confirmed_by, reason)
                for row in by_id[fid]:
                    if row.get("confirmed") != confirmed or row.get("confirmed_by") != cb:
                        row["confirmed"] = confirmed
                        row["confirmed_by"] = cb
                        applied += 1
    if applied:
        _write_tsv(fp, FACT_FIELDS, rows)
    return applied


def ingest_followups(session_dir):
    """读 followups.tsv（Verifier 发现"证据缺口而非硬性分歧"时追加写入），为每条尚未入队的记录
    在 worklist 新增一张 source=followup 的卡，重新进入 L1 drive 队列——防止"缺证据"静默沉底为
    永久 unconfirmed（业界 AGENTS 框架吸收：follow-up loop）。"""
    session = Path(session_dir)
    fp = session / "followups.tsv"
    if not fp.exists():
        return 0
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        build_worklist(session_dir)
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    existing_ids = {r["card_id"] for r in rows}
    with fp.open(encoding="utf-8", newline="") as f:
        fu_rows = list(csv.DictReader(f, delimiter="\t"))
    added = 0
    for fu in fu_rows:
        fid = (fu.get("followup_id") or "").strip()
        if not fid or fid in existing_ids:
            continue
        sink_type = fu.get("sink_type") or ""
        rows.append({
            "card_id": fid,
            "basis_id": fu.get("basis_id") or "",
            "direction": "backward",
            "sink_type": sink_type,
            "module": "",
            "band": str(_band(sink_type)),
            "status": "unchecked",
            "depends_on": "",
            "source": "followup",
            "must_through": "",
            "entry_types": "",
            "component": "",
            "has_bypass": "",
        })
        existing_ids.add(fid)
        added += 1
    if added:
        _write_tsv(wl_path, WL_FIELDS, rows)
    return added


def _followup_gap_descriptions(session_dir, nxt_cards):
    fp = Path(session_dir) / "followups.tsv"
    if not fp.exists():
        return []
    ids = {c["card_id"] for c in nxt_cards if c.get("source") == "followup"}
    if not ids:
        return []
    with fp.open(encoding="utf-8", newline="") as f:
        fu_rows = list(csv.DictReader(f, delimiter="\t"))
    out = []
    for fu in fu_rows:
        fid = (fu.get("followup_id") or "").strip()
        if fid in ids:
            out.append("FOLLOWUP\t%s\t%s" % (fid, fu.get("gap_description", "")))
    return out


def rejected_fact_count(session_dir):
    rj = Path(session_dir) / "facts-rejected.tsv"
    if not rj.exists():
        return 0
    with rj.open(encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f, delimiter="\t"))


def worklist_counts(session_dir):
    session = Path(session_dir)
    wl = session / "worklist.tsv"
    out = {"unchecked": 0}
    if not wl.exists():
        return out
    with wl.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            st = row.get("status") or "unchecked"
            out[st] = out.get(st, 0) + 1
    out["unchecked"] = out.get("unchecked", 0)
    return out


def final_status(session_dir):
    """机械终态判定：审计是否真正完成，不依赖主代理自己转述结论。

    真实审计中发现：主代理在最终汇报里向用户声称"gate-1.py: pass、审计完成"，但
    同一 session 目录里 gate-1.py 自己产出的 gate_record.md 明明白白写着
    `gate_result: rework`——这不是分析质量问题，是诚实性问题：现有机制没有任何东西
    阻止主代理在自然语言汇报里编造一个和机械产物矛盾的结论。

    这个函数产出一个任何人都能独立复验的机械判定，不涉及任何语义推理，只做纯粹的
    文件读取与比对。`report-delivery` 要求报告生成前必须运行这个判定并把结果原样
    写入报告，不允许由主代理凭记忆转述或改写这个结论。

    判定条件（全部满足才是 COMPLETED_VERIFIED，任一不满足则明确指出具体原因，不
    允许模糊的"基本完成"这类中间态）：
    1. worklist.tsv 存在且 UNCHECKED == 0；
    2. check_point_ledger.tsv 里没有遗留"未检查"终态；
    3. gate_record.md 存在，且其 `gate_result:` 字段字面等于 pass；
    4. gate_record.md 的文件修改时间不早于 worklist.tsv 与 check_point_ledger.tsv——
       防止引用一次过期的 pass 结论（账本后续又被改动过，那份 pass 已经不代表当前状态）；
    5. 没有残留的可疑模板化证据（detect_templated_evidence 非空即视为未完成，须先
       retract 受影响的事实、重开受影响的卡、重新做真实分析，才允许再次判定完成）。
    """
    session = Path(session_dir)
    reasons = []

    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        return "NOT_COMPLETE: worklist.tsv 不存在"
    unchecked = worklist_counts(session_dir).get("unchecked", 0)
    if unchecked > 0:
        reasons.append("worklist.tsv 仍有 %d 张未闭合卡" % unchecked)

    led_path = session / "check_point_ledger.tsv"
    if not led_path.exists():
        reasons.append("check_point_ledger.tsv 不存在")
    else:
        with led_path.open(encoding="utf-8", newline="") as f:
            led_rows = list(csv.DictReader(f, delimiter="\t"))
        residual = sum(1 for r in led_rows if (r.get("terminal_state") or "") in ("", "未检查"))
        if residual > 0:
            reasons.append("check_point_ledger.tsv 仍有 %d 个检查点终态为「未检查」" % residual)

    gr_path = session / "gate_record.md"
    if not gr_path.exists():
        reasons.append("gate_record.md 不存在（说明宿主从未执行过 gate-1.py 全量对账）")
    else:
        gr_text = gr_path.read_text(encoding="utf-8", errors="replace")
        if "gate_result: pass" not in gr_text:
            m = [l for l in gr_text.splitlines() if l.startswith("gate_result:")]
            reasons.append("gate_record.md 的 gate_result 不是 pass（实际：%s）" % (m[0] if m else "未找到 gate_result 字段"))
        else:
            gr_mtime = gr_path.stat().st_mtime
            for stale_path in (wl_path, led_path):
                if stale_path.exists() and stale_path.stat().st_mtime > gr_mtime:
                    reasons.append("gate_record.md 的 pass 结论已过期（%s 在其之后又被修改过，需重新跑 gate-1.py）" % stale_path.name)
                    break

    templated = detect_templated_evidence(session_dir)
    if templated:
        reasons.append("检测到 %d 组疑似模板化伪造证据，须先 retract 并重新真实分析" % len(templated))

    if reasons:
        return "NOT_COMPLETE: " + "; ".join(reasons)
    return "COMPLETED_VERIFIED"


LARGE_SCALE_PRUNING_THRESHOLD = 300


def _large_scale_pruning_notice(session_dir, unchecked):
    """规模守卫：高危 sink 绝不因为这条提醒被阻塞或推迟。

    只统计**低危（band 2）**未闭合卡的规模，只对低危部分建议类级剪枝提效率；高危
    band(0/1) 的 sink 必须立即进入真实 Analyzer 分析，不受这条规模提示影响。消息里
    明确写清楚"这条建议只针对低危噪音类，高危 sink 应该已经在并行做真实分析，不要
    因为这条提示暂停高危分析"，避免主代理误读成"整个项目都要先剪枝"。"""
    wl_path = Path(session_dir) / "worklist.tsv"
    if not wl_path.exists():
        return None
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    low_risk_unchecked = sum(
        1 for r in rows
        if r.get("status") in ("", "unchecked", None) and _band(r.get("sink_type")) not in HIGH_RISK_BANDS
    )
    if low_risk_unchecked < LARGE_SCALE_PRUNING_THRESHOLD:
        return None
    pl_path = Path(session_dir) / "pruning_ledger.tsv"
    if pl_path.exists():
        with pl_path.open(encoding="utf-8", newline="") as f:
            if len(list(csv.DictReader(f, delimiter="\t"))) > 0:
                return None
    return ("NOTICE=LARGE_SCALE_LOW_RISK_NO_PRUNING_YET low_risk_unchecked=%d threshold=%d "
            "— 仅针对低危噪音类（非反序列化/SQL注入/XXE/越权/命令执行等高危 band）：可派 "
            "Summarizer（agents/class-pruner-prompt.md）做类级剪枝提效率；**高危 sink 不受此提示影响，"
            "应已在并行做真实 Analyzer 五步分析，不要因为这条提示暂停高危分析**（见 "
            "candidate-discovery/SKILL.md 9c0 节）") % (low_risk_unchecked, LARGE_SCALE_PRUNING_THRESHOLD)


def _evidence_for_reason(session, reason, basis_id):
    """尽量把 worklist 的 reason 转成携带真实 file:line 的引用：gate-1.py 的
    「禁批量采样闭合」用正则找 file:line 或 clusters/ 引用，纯 fact_id/wu_id 追溯串不满足
    这个格式。找不到真实证据就原样返回内部追溯串（信息不丢失，只是那条特定正则可能识别
    不到，不影响 session.py 自身功能）。"""
    if not reason:
        return reason
    if reason.startswith("shard:"):
        wu_id = reason.split(":", 1)[1]
        for shard in session.glob("batches/**/%s.tsv" % wu_id):
            try:
                with shard.open(encoding="utf-8", newline="") as f:
                    for rec in csv.DictReader(f, delimiter="\t"):
                        if (rec.get("sink_id") or rec.get("basis_id")) == basis_id:
                            refs = (rec.get("evidence_refs") or "").split(",")[0].strip()
                            if refs:
                                return "%s(%s)" % (reason, refs)
            except (OSError, csv.Error):
                pass
        return reason
    if ":fact=" in reason:
        fact_id = reason.rsplit("=", 1)[1]
        fp = session / "facts.tsv"
        if fp.exists():
            with fp.open(encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f, delimiter="\t"):
                    if r.get("fact_id") == fact_id:
                        ev = r.get("evidence") or ""
                        if ev:
                            return "%s(%s)" % (reason, ev)
        return reason
    return reason


def sync_check_point_ledger(session_dir):
    """把 worklist.tsv 的终态同步回 check_point_ledger.tsv。

    真实 Tomcat 审计发现的结构性断层：`session.py drive` 整套机制只在 `build_worklist`
    时读一次 `check_point_ledger.tsv`，之后全部状态只写进 `worklist.tsv`——
    `check_point_ledger.tsv` 的 `terminal_state` 永远停在派生时的「未检查」。这导致：
    1. `gate-1.py` 的核心等式「planned==terminal」对任何走 drive 的真实审计必然 FAIL
       （账本里没有一行真正"terminal"）；
    2. 「禁批量采样闭合」这条本该拦截伪造批量闭合的 gate 完全失效——它检查账本 reason
       列是否带真实引用，但账本从未被更新过，reason 永远为空，检查逻辑整段被跳过。
    真实审计验证：主代理绕开 Analyzer 子代理，自己写 Python 脚本一次性给 7835+ 张卡编造
    模板化假证据（"source=safe_at_class_level|..."），这条 gate 完全没有反应，因为它看的
    账本压根没被更新。

    每次 drive 后调用，只更新有真实终态变化的行；reason 尽量携带可反查的真实 evidence
    （通过 `_evidence_for_reason` 从 shard/facts.tsv 拉取）。"""
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    led_path = session / "check_point_ledger.tsv"
    if not wl_path.exists() or not led_path.exists():
        return 0
    with wl_path.open(encoding="utf-8", newline="") as f:
        wl_rows = list(csv.DictReader(f, delimiter="\t"))
    by_cpid = {r["card_id"]: r for r in wl_rows}
    with led_path.open(encoding="utf-8", newline="") as f:
        led_rows = list(csv.reader(f, delimiter="\t"))
    if not led_rows:
        return 0
    header = led_rows[0]
    try:
        i_cpid = header.index("check_point_id")
        i_term = header.index("terminal_state")
        i_reason = header.index("reason")
        i_concl = header.index("concluded_at")
    except ValueError:
        return 0
    synced = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for row in led_rows[1:]:
        if len(row) <= max(i_cpid, i_term, i_reason, i_concl):
            continue
        card = by_cpid.get(row[i_cpid])
        if not card:
            continue
        status = card.get("status") or ""
        if status in ("", "unchecked"):
            continue
        reason = _evidence_for_reason(session, card.get("reason") or "", card.get("basis_id") or "")
        if row[i_term] != status or row[i_reason] != reason:
            row[i_term] = status
            row[i_reason] = reason
            row[i_concl] = now
            synced += 1
    if synced:
        with led_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerows(led_rows)
    return synced


def _load_inventory_by_id(session_dir, filename, id_field):
    """读取一份冻结清单（sink/source/file_inventory.tsv），按其 ID 列建索引。
    文件不存在时返回空字典（调用方按"查不到"处理，不崩溃）。"""
    path = Path(session_dir) / filename
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {r.get(id_field): r for r in csv.DictReader(f, delimiter="\t")}


def _relativize_path(path, file_by_path):
    """把可能是绝对路径的 file 路径归一化成 file_inventory.tsv 里的相对路径形式。

    真实 dvpwa 冒烟跑暴露的问题：Analyzer 给文件级候选写 evidence_refs 时用了完整
    绝对路径（如 `/Users/xxx/dvpwa/Dockerfile.app:1-20`），而 file_inventory.tsv 里
    存的是相对路径（`Dockerfile.app`）——两者不匹配导致 gate[候选 ID 反查] 的文件级
    豁免规则永远命中不上（18 个候选里 15 个因此 FAIL）。优先精确匹配；查不到则退化
    为按路径结尾做后缀匹配（绝对路径以某个清单相对路径结尾时采用该相对路径）；
    两者都查不到时原样返回，不假装能解析。"""
    if not path:
        return path
    if path in file_by_path:
        return path
    for rel in file_by_path:
        if rel and (path == rel or path.endswith("/" + rel)):
            return rel
    return path


_NEW_REF_RE = re.compile(r'^[A-Za-z0-9_./-]+:\d')


def _split_refs(evidence_refs):
    """把 evidence_refs 拆成独立的 file:line 引用列表。

    真实数据核实过两种互相矛盾的写法都存在：分号常用于分隔不同文件（如
    "app.py:35; course.jinja2:14,22"），但也见过用逗号分隔不同文件（如
    "student.py:41-45,views.py:52-57"）；同时逗号也用于同一文件内的多行号列表
    （如 "course.jinja2:3,9,14,15,22,49" 是一个文件六个行号，不是六个文件）。
    纯按分隔符切分无法同时处理这两种写法——用启发式区分：先按分号切出大段，
    每段内再按逗号试切，逗号后的部分若本身长得像一个新引用（`路径:数字` 开头，
    正则 `_NEW_REF_RE`），才当作独立的新引用；否则视为同一文件的行号延续，
    合并回当前引用（不产生"路径不完整"的假引用）。"""
    text = (evidence_refs or "").strip()
    if not text:
        return []
    refs = []
    for seg in (s.strip() for s in text.split(";") if s.strip()):
        parts = seg.split(",")
        cur = parts[0]
        for part in parts[1:]:
            part = part.strip()
            if _NEW_REF_RE.match(part):
                if cur.strip():
                    refs.append(cur.strip())
                cur = part
            else:
                cur = cur + "," + part
        if cur.strip():
            refs.append(cur.strip())
    return refs


def _location_for_basis(evidence_refs, basis_id, file_by_path):
    """从 evidence_refs 的多个引用里，挑出真正属于本候选（basis_id 对应文件）的那条。

    真实 dvpwa 冒烟跑暴露的问题（两层）：
    1. 多位置候选（如一个 XSS 根因触发点在 app.py，实例分别落在多个模板文件）的
       evidence_refs 用 "; " 分隔多个引用，此前只按逗号切分，整段被当成一个
       location 塞入 candidates.tsv，污染 path/start_line/end_line 三列。
    2. 即使正确拆分成多条引用，"取第一条"仍然选错——这类候选的 evidence_refs 习惯
       把共同根因位置（app.py:35）排在最前面，本候选自己真正对应的文件（如
       course.jinja2:14）反而排在后面；每个候选在 worklist 里的 basis_id 就是它
       自己对应的那个文件，应该优先选中与 basis_id 匹配的那条引用，而不是盲目取
       列表第一条。

    找不到与 basis_id 匹配的引用时，退化为取第一条（保底不空手），一条引用都没有
    时返回空字符串（调用方再退化为 basis_id:1）。"""
    refs = _split_refs(evidence_refs)
    if not refs:
        return ""
    norm_basis = _relativize_path(basis_id, file_by_path)
    for ref in refs:
        ref_path = ref.split(":", 1)[0].strip()
        if _relativize_path(ref_path, file_by_path) == norm_basis:
            return ref
    return refs[0]


def _derive_candidate_id(row, sink_by_id, source_by_id, file_by_path):
    """按 contracts/data-structures/candidate-finding.md #60 行公式推导 candidate_id：
    `C-{sink_seq}-{source_seq}-{sig8}`。

    真实 dvpwa 冒烟跑暴露的问题：这个公式此前完全没有机械实现，candidate_id 的推导
    （查 sort_order、算 md5）全靠 LLM 手工完成——真实运行中代理干脆没做，report-delivery
    阶段拿不到规范 candidate_id，只能自己发明 V01/V02 这种序号当文件名。

    三种情况（对应 worklist 的三种 direction）：
    - backward（sink 锚定）：sink_seq 来自 sink_inventory 的 sort_order，
      source_seq 来自 worklist `source` 列指向的 source_inventory 条目（查不到则 0），
      sig8 = md5(file:line:sink_type) 前 8 位。
    - forward（source 锚定，无 sink 命中）：source_seq 来自 source_inventory，
      按文档显式 fallback，sink_seq 取该候选所在文件的文件终态检查点排序序（即
      file_inventory 该文件的 sort_order），sig8 = md5(file:line) 前 8 位（省略 sink_type）。
    - terminal（文件级终态，无 sink 无 source）：basis_id 本身就是文件路径，
      sink_seq 同样取 file_inventory 排序序，source_seq 置 0，
      sig8 = md5(location) 前 8 位，location 优先取 evidence_refs 里的第一个真实
      file:line（多位置候选按 _first_location_ref 只取第一个，见其 docstring）。

    路径可能是绝对路径（Analyzer 写证据习惯用完整路径）也可能是相对路径（清单里的
    形式）——涉及 file_inventory 查找/比对的地方一律先经 _relativize_path 归一化。

    返回 (candidate_id, location)。"""
    basis_id = row.get("basis_id", "") or ""
    direction = row.get("direction", "") or ""
    sink_type = row.get("sink_type", "") or ""

    def _seq(r):
        try:
            return int((r or {}).get("sort_order") or 0)
        except (TypeError, ValueError):
            return 0

    if direction == "backward" and basis_id in sink_by_id:
        sink_row = sink_by_id[basis_id]
        sink_seq = _seq(sink_row)
        location = sink_row.get("file:line", "") or ""
        source_row = source_by_id.get(row.get("source", ""))
        source_seq = _seq(source_row)
        sig = hashlib.md5((location + ":" + sink_type).encode()).hexdigest()[:8]
    elif direction == "forward" and basis_id in source_by_id:
        source_row = source_by_id[basis_id]
        source_seq = _seq(source_row)
        location = source_row.get("file:line", "") or ""
        file_path = _relativize_path(location.split(":", 1)[0], file_by_path)
        sink_seq = _seq(file_by_path.get(file_path))
        sig = hashlib.md5(location.encode()).hexdigest()[:8]
    else:
        # terminal：basis_id 本身是文件路径；location 优先用 evidence_refs 里真正
        # 属于本候选（与 basis_id 匹配）的那条引用，basis_id 本身也可能是绝对路径，
        # 一并归一化后再查排序序
        norm_basis = _relativize_path(basis_id, file_by_path)
        sink_seq = _seq(file_by_path.get(norm_basis))
        source_seq = 0
        matched_ref = _location_for_basis(row.get("evidence_refs"), basis_id, file_by_path)
        if matched_ref:
            ref_path, _, ref_line = matched_ref.rpartition(":")
            norm_ref_path = _relativize_path(ref_path, file_by_path) if ref_path else ref_path
            location = (norm_ref_path + ":" + ref_line) if ref_path else matched_ref
        else:
            location = norm_basis + ":1"
        sig = hashlib.md5(location.encode()).hexdigest()[:8]

    return "C-%05d-%05d-%s" % (sink_seq, source_seq, sig), location


def sync_candidates_tsv(session_dir):
    """机械生成/合并 candidates.tsv——真实 dvpwa 冒烟跑暴露的核心缺口：这份阶段1
    权威产物此前从未被机械生成过，candidate_id 的确定性推导完全靠 LLM 手算，真实
    运行里代理干脆跳过，report-delivery 只能自己发明 V01/V02 这种序号当文件名，
    与 gate 依赖的候选 ID 反查/三事实源一致性等方程全部脱节。

    只读 worklist.tsv 的 candidate 状态卡机械投影 discovery 段字段（candidate_id/
    location/sink_type/path/start_line/end_line/discovery_source/discovery_reasoning_note）
    ——不做语义判断，root_cause_group_id/severity_hypothesis_initial 等语义字段仍需
    上游角色填写，此处留空好过编造。

    幂等 + 冻结语义：discovery 字段创建后不可变（见 candidate-finding.md #24 行），
    已存在的 candidate_id 不重新计算/覆盖，只追加新出现的候选；下游字段（verdict/
    lifecycle_state/report_record_ref 等）由阶段2/3 各自写权限方回填，本函数完全
    不碰这些列，重复调用不会抹掉阶段2/3 已经写入的结论。"""
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        return 0
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    candidates = [r for r in rows if r.get("status") == "candidate"]

    cand_path = session / "candidates.tsv"
    existing = []
    existing_ids = set()
    if cand_path.exists():
        with cand_path.open(encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f, delimiter="\t"))
        existing_ids = {r.get("candidate_id") for r in existing}

    sink_by_id = _load_inventory_by_id(session_dir, "sink_inventory.tsv", "sink_id")
    source_by_id = _load_inventory_by_id(session_dir, "source_inventory.tsv", "source_id")
    file_by_path = _load_inventory_by_id(session_dir, "file_inventory.tsv", "path")

    added = 0
    for r in candidates:
        cid, location = _derive_candidate_id(r, sink_by_id, source_by_id, file_by_path)
        if cid in existing_ids:
            continue
        path, _, line = location.rpartition(":")
        existing.append({
            "candidate_id": cid,
            "location": location,
            "sink_type": r.get("sink_type", ""),
            "severity_hypothesis_initial": "",
            "root_cause_group_id": "",
            "lifecycle_state": "created",
            "verdict": "",
            "cluster_ref": "",
            "verification_record_ref": "",
            "report_record_ref": "",
            "created_at": "",
            "discovery_source": "pattern_driven",
            "path": path or location,
            "start_line": line or "",
            "end_line": line or "",
            "discovery_reasoning_note": r.get("evidence_summary", "") or "(见对应 batches/ 分片原始证据)",
        })
        existing_ids.add(cid)
        added += 1
    _write_tsv(cand_path, CAND_FIELDS, existing)
    return added


VERDICT_VALUES = {"confirmed", "refuted", "informational", "suppressed"}


def ingest_verification_shards(session_dir):
    """归并阶段2 Verifier 的验证结论分片到 candidates.tsv 的 verdict/lifecycle_state/
    verification_record_ref 三列。

    真实 dvpwa 冒烟跑暴露的问题：阶段2 只把验证结论写进 verification-summary.md，
    从未同步回 candidates.tsv 自己的 verdict 列——这份列因此在真实运行里全程为空。
    后果很隐蔽：gate[V 文件候选映射] 因为找不到任何 verdict=confirmed 的行而空转
    通过（真实 bug 完全没被这条方程抓到），阶段3 report-delivery 早期派发也因为拿
    不到 candidates.tsv 里的确认状态，自己简化了 finding 文件名规则。

    修法同构 Confirmer/Summarizer 分片模式：Verifier 只写自己的分片
    `verification_shards/{verifier_id}-verdicts.tsv`（表头
    `candidate_id\\tverdict\\tverification_record_ref`），不直接改 candidates.tsv；
    drive 统一按 candidate_id 应用（只更新这三列，不新增行——candidate_id 必须已
    存在于 candidates.tsv，否则跳过，因为 discovery 段的创建权只属于阶段1）。
    """
    session = Path(session_dir)
    shard_dir = session / "verification_shards"
    if not shard_dir.exists():
        return 0
    cand_path = session / "candidates.tsv"
    if not cand_path.exists():
        return 0
    with cand_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    by_id = {r.get("candidate_id"): r for r in rows}

    applied = 0
    for shard in sorted(shard_dir.glob("*-verdicts.tsv")):
        with shard.open(encoding="utf-8", newline="") as f:
            for rec in csv.DictReader(f, delimiter="\t"):
                cid = (rec.get("candidate_id") or "").strip()
                verdict = (rec.get("verdict") or "").strip()
                if not cid or cid not in by_id or verdict not in VERDICT_VALUES:
                    continue
                row = by_id[cid]
                vref = rec.get("verification_record_ref") or ""
                if row.get("verdict") != verdict or row.get("verification_record_ref") != vref:
                    row["verdict"] = verdict
                    row["verification_record_ref"] = vref
                    if row.get("lifecycle_state") in ("", "created"):
                        row["lifecycle_state"] = "verified"
                    applied += 1
    _write_tsv(cand_path, CAND_FIELDS, rows)
    return applied


def _evidence_headline(evidence_summary):
    """从 five_segment_evidence 里抽取 sink 段作为一句话摘要。

    发现问题：此前 live_findings_index.md 每行只有 "shard:WU-0009" 这种批次指针，
    Analyzer 实际写下的 five_segment_evidence（真正描述"这是什么漏洞"的文本）被
    直接丢弃——用户打开索引文件看不出任何一条 candidate 具体是什么问题，必须自己
    去翻 batches/ 目录下的原始 TSV。找不到 sink 段时退化为截断原文，不留空，保证
    任何时候都有可读内容。"""
    text = evidence_summary or ""
    for seg in text.split("|"):
        seg = seg.strip()
        if seg.startswith("sink:"):
            headline = seg[len("sink:"):].strip()
            return headline if headline else "(sink 描述为空)"
    return (text[:80] + "...") if len(text) > 80 else (text or "(无证据文本，检查该批 Analyzer 输出)")


def sync_live_findings_index(session_dir):
    """自动维护 live_findings_index.md，保证候选发现实时可见且可读。

    此前这份文件完全靠主代理自己记得手写更新——同类"靠 LLM 记忆而非机制强制"的问题
    这次会话已经修过好几处（pruning_ledger 同步、facts 分片归并等），这里补上最后一处：
    每次 drive 后机械重新生成，保证任何时刻查看这份文件都反映当前真实的 candidate 列表，
    不需要等主代理"想起来"去写。只读 worklist.tsv 的 candidate 状态卡，不做语义判断
    （不重新判断真实性/严重度，那是阶段2的工作）。

    真实运行中发现：仅有 card_id/basis_id/reason 字段时，reason 只是 "shard:WU-0009"
    这种批次指针，用户打开文件完全看不出发现了什么漏洞，等同没有实时输出。现在带上
    file:line（evidence_refs）和一句话摘要（从 five_segment_evidence 的 sink 段抽取），
    使这份文件本身就是一份（未经阶段2定级的）可读漏洞速览，而不仅是一份卡片 ID 索引。"""
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        return 0
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    candidates = [r for r in rows if r.get("status") == "candidate"]
    lines = [
        "# 实时候选发现索引（live_findings_index.md，机械自动维护，非最终报告）",
        "",
        "本文件每次 `session.py drive` 后自动重新生成，反映当前真实的 candidate 状态；",
        "候选是否最终成立、严重度定级由阶段2验证与定级决定，本文件只做机械投影。",
        "",
        "| card_id | sink_type | band | file:line | 摘要（来自 Analyzer 证据 sink 段） | 溯源 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in sorted(candidates, key=lambda r: (_band(r.get("sink_type")), r.get("card_id") or "")):
        loc = r.get("evidence_refs", "") or r.get("basis_id", "")
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r.get("card_id", ""), r.get("sink_type", ""),
            _band(r.get("sink_type")), loc.replace("|", "/"),
            _evidence_headline(r.get("evidence_summary", "")).replace("|", "/"),
            r.get("reason", "").replace("|", "/"),
        ))
    lines.append("")
    lines.append("总计：%d 个 candidate（截至本次 drive）。" % len(candidates))
    (session / "live_findings_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(candidates)


def drive(session_dir, limit=10):
    if not (Path(session_dir) / "worklist.tsv").exists():
        build_worklist(session_dir)
    ingested = ingest_shards(session_dir)
    summarizer_ingested = ingest_summarizer_shards(session_dir)
    confirmer_ingested = ingest_confirmer_shards(session_dir)
    followups = ingest_followups(session_dir)
    closed = apply_facts(session_dir)
    rejected = rejected_fact_count(session_dir)
    woken = wake_blocked_cards(session_dir)
    n = worklist_counts(session_dir).get("unchecked", 0)
    synced = sync_check_point_ledger(session_dir)
    live_candidates = sync_live_findings_index(session_dir)
    candidates_added = sync_candidates_tsv(session_dir)
    verdicts_applied = ingest_verification_shards(session_dir)
    lines = ["INGESTED=%d" % ingested, "SUMMARIZER_INGESTED=%d" % summarizer_ingested, "CONFIRMER_INGESTED=%d" % confirmer_ingested, "FOLLOWUPS_INGESTED=%d" % followups, "REWRITE_CLOSED=%d" % len(closed), "REJECTED_FACTS=%d" % rejected, "WOKEN=%d" % len(woken), "LEDGER_SYNCED=%d" % synced, "LIVE_CANDIDATES=%d" % live_candidates, "CANDIDATES_TSV_SYNCED=%d" % candidates_added, "VERDICTS_APPLIED=%d" % verdicts_applied, "UNCHECKED=%d" % n]
    templated = detect_templated_evidence(session_dir)
    for ev, count in templated[:5]:
        lines.append("NOTICE=SUSPECTED_TEMPLATED_EVIDENCE count=%d evidence=%s" % (count, ev[:120]))
    if n == 0:
        lines.insert(0, "STATE=L1_CLOSED")
        if templated:
            # 真实 dvpwa 冒烟跑暴露：STATE=L1_CLOSED 时即使还挂着未处理的
            # SUSPECTED_TEMPLATED_EVIDENCE（真实运行中一次挂了 5 组、共 315 张卡从未
            # retract），drive() 自己的 ALLOW= 行此前完全不看这个信号，直接放行
            # completed——主代理只看 ALLOW= 就会误以为"可以收尾了"，即使
            # final_status() 最终会拦下来，中间这层不一致给了自我辩解的空子
            # （"drive 说 ALLOW=completed 啊"）。有未处理的模板化证据时，明确
            # FORBIDDEN=completed，把"必须先 retract"这件事提到跟 UNCHECKED>0
            # 同等优先级的位置，不能只靠 final_status 事后兜底。
            lines.append("FORBIDDEN=completed")
            lines.append("NOTICE=RETRACT_REQUIRED_BEFORE_COMPLETED — 上面的 SUSPECTED_TEMPLATED_EVIDENCE 未处理前禁止声明完成")
        else:
            lines.append("ALLOW=stage2,stage3,completed")
    else:
        nxt = next_wu(session_dir, limit)
        lines.insert(0, "STATE=NEED_ANALYZE")
        lines.append("FORBIDDEN=completed,stage2,stage3")
        pruning_notice = _large_scale_pruning_notice(session_dir, n)
        if pruning_notice:
            lines.append(pruning_notice)
        lines.append("NEXT=" + ",".join(c["card_id"] for c in nxt))
        for c in nxt:
            lines.append("CARD\t%s\t%s\t%s" % (c["card_id"], c.get("basis_id", ""), c.get("sink_type", "")))
        lines.extend(_context_lines(session_dir, nxt))
        lines.extend(_followup_gap_descriptions(session_dir, nxt))
    Path(session_dir, "drive_state.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def _row_to_card(row):
    mt = [x for x in (row.get("must_through") or "").split(";") if x]
    ets = [x for x in (row.get("entry_types") or "").split(";") if x]
    return {
        "card_id": row["card_id"],
        "kind": "sink",
        "sink_id": row.get("basis_id"),
        "sink_type": row.get("sink_type"),
        "module": row.get("module"),
        "status": row.get("status"),
        "must_through": mt or None,
        "entry_types": ets or None,
        "component": row.get("component") or None,
        "has_bypass": row.get("has_bypass") == "true",
        "depends_on": [x for x in (row.get("depends_on") or "").split(";") if x],
    }


def _row_to_fact(row):
    confirmed = str(row.get("confirmed") or "").lower() == "true"
    return {
        "fact_id": row.get("fact_id"),
        "type": row.get("type"),
        "source_role": (row.get("source_role") or "").strip().lower(),
        "scope": row.get("scope"),
        "sink_type": row.get("sink_type"),
        "function": row.get("function"),
        "component": row.get("component"),
        "src": row.get("src"),
        "dst": row.get("dst"),
        "sink_id": row.get("sink_id"),
        "blocks": row.get("blocks"),
        "evidence": row.get("evidence"),
        "confirmed": confirmed,
    }


def _quarantine_rejected(session, rejected):
    if not rejected:
        return
    rj_path = session / "facts-rejected.tsv"
    fields = FACT_FIELDS + ["reject_reason"]
    existing = []
    if rj_path.exists():
        with rj_path.open(encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f, delimiter="\t"))
    for row, reason in rejected:
        r = dict(row)
        r["reject_reason"] = reason
        existing.append(r)
    _write_tsv(rj_path, fields, existing)


def apply_facts(session_dir):
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        build_worklist(session_dir)
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    facts = []
    fp = session / "facts.tsv"
    if fp.exists():
        with fp.open(encoding="utf-8", newline="") as f:
            raw_facts = list(csv.DictReader(f, delimiter="\t"))
        valid_facts, rejected = split_valid_facts(raw_facts)
        _quarantine_rejected(session, rejected)
        if rejected:
            _write_tsv(fp, FACT_FIELDS, valid_facts)
        facts = [_row_to_fact(r) for r in valid_facts]
    cards = [_row_to_card(r) for r in rows]
    patches = {p["card_id"]: p for p in apply_rewrite(cards, facts)}
    closed = []
    for row in rows:
        p = patches.get(row["card_id"])
        if not p:
            continue
        row["status"] = p["terminal_state"]
        row["reason"] = p.get("reason", "")
        closed.append(row["card_id"])
    _write_tsv(wl_path, WL_FIELDS, rows)
    return closed


def _confirmed_symbols(session_dir):
    """收集本轮所有 confirmed=true 事实涉及的符号（function/src/dst），
    供 wake_blocked 判断哪些 blocked 卡应重新唤醒。"""
    fp = Path(session_dir) / "facts.tsv"
    symbols = set()
    if not fp.exists():
        return symbols
    with fp.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        if str(r.get("confirmed") or "").lower() != "true":
            continue
        for key in ("function", "src", "dst"):
            v = (r.get(key) or "").strip()
            if v:
                symbols.add(v)
    return symbols


def wake_blocked_cards(session_dir):
    """用本轮新增的 confirmed 事实符号唤醒 status=blocked 的卡（重开为 unchecked）。
    仅作用于 Analyzer 因证据不足而 blocked 的卡，不作用于 K 规则 blocked_at 的终态闭合卡。"""
    session = Path(session_dir)
    wl_path = session / "worklist.tsv"
    if not wl_path.exists():
        return []
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    symbols = _confirmed_symbols(session_dir)
    if not symbols:
        return []
    cards = [_row_to_card(r) for r in rows]
    woken = wake_blocked(cards, symbols)
    woken_ids = {c["card_id"] for c in woken}
    if not woken_ids:
        return []
    for row in rows:
        if row["card_id"] in woken_ids:
            row["status"] = "unchecked"
            row["reason"] = ""
    _write_tsv(wl_path, WL_FIELDS, rows)
    return sorted(woken_ids)


def _context_lines(session_dir, nxt_cards):
    """为下一批 NEXT 卡生成 CONTEXT= 摘要行：列出与这批卡 sink_type/component 相关的
    已 confirmed 事实，供主代理派发时直接带给 Analyzer，避免重复推导已确认的结论。"""
    fp = Path(session_dir) / "facts.tsv"
    if not fp.exists() or not nxt_cards:
        return []
    sink_types = {c.get("sink_type") for c in nxt_cards if c.get("sink_type")}
    components = {c.get("component") for c in nxt_cards if c.get("component")}
    with fp.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = []
    for r in rows:
        if str(r.get("confirmed") or "").lower() != "true":
            continue
        relevant = (
            (r.get("sink_type") or "") in sink_types
            or (r.get("component") or "") in components
        )
        if not relevant:
            continue
        t = r.get("type", "")
        key = r.get("function") or r.get("component") or r.get("scope") or r.get("src") or ""
        out.append("CONTEXT\t%s\t%s\t%s" % (t, key, r.get("evidence", "")))
    return out


def explosion_radius(session_dir):
    """按 reason 分组统计每条已确认事实消掉了多少张卡（爆炸半径），供 A2 复核按影响面
    优先级排序——半径越大，一旦该事实是误判，连坐消掉的卡越多，越应优先复核。
    只统计 K 规则的级联消卡（reason 含 `:fact=`），shard 单卡判定（reason 以 `shard:` 开头）
    半径恒为 1，不算级联，不进本统计。"""
    wl_path = Path(session_dir) / "worklist.tsv"
    if not wl_path.exists():
        return []
    with wl_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    groups = {}
    for row in rows:
        reason = row.get("reason") or ""
        if ":fact=" not in reason:
            continue
        groups.setdefault(reason, []).append(row["card_id"])
    out = [{"reason": r, "count": len(ids), "cards": sorted(ids)} for r, ids in groups.items()]
    out.sort(key=lambda x: (-x["count"], x["reason"]))
    return out


def retract(session_dir, fact_id):
    """撤回一条已确认事实：置 confirmed=false（对未来 apply_rewrite 失效），
    并按 reason 里的 `fact=<fact_id>` 反查该事实曾消掉的全部卡，重开为 unchecked——
    不需要整跑重扫，级联半径本身就是可追溯的（D0 reason 统一格式是本功能的前提）。
    返回 (found_fact: bool, reopened_card_ids: list)。"""
    session = Path(session_dir)
    fp = session / "facts.tsv"
    found = False
    if fp.exists():
        with fp.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        for r in rows:
            if r.get("fact_id") == fact_id:
                r["confirmed"] = "false"
                found = True
        if found:
            _write_tsv(fp, FACT_FIELDS, rows)
    wl_path = session / "worklist.tsv"
    reopened = []
    if wl_path.exists():
        with wl_path.open(encoding="utf-8", newline="") as f:
            wl_rows = list(csv.DictReader(f, delimiter="\t"))
        marker = "fact=%s" % fact_id
        for row in wl_rows:
            if marker in (row.get("reason") or ""):
                row["status"] = "unchecked"
                row["reason"] = ""
                reopened.append(row["card_id"])
        if reopened:
            _write_tsv(wl_path, WL_FIELDS, wl_rows)
    return found, sorted(reopened)


def next_wu(session_dir, limit=10):
    session = Path(session_dir)
    wl = session / "worklist.tsv"
    if not wl.exists():
        build_worklist(session_dir)
    with wl.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    cards = []
    for r in rows:
        c = dict(r)
        c["status"] = r.get("status")
        cards.append(c)
    return order_cards(cards)[:limit]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "apply", "next", "drive", "status", "radius", "retract", "final-status"])
    ap.add_argument("--session", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--fact", default=None, help="fact_id to retract (cmd=retract)")
    args = ap.parse_args()
    if args.cmd == "build":
        print("worklist_rows", build_worklist(args.session))
    elif args.cmd == "apply":
        print("closed", ",".join(apply_facts(args.session)))
    elif args.cmd == "status":
        c = worklist_counts(args.session)
        print("UNCHECKED=%d" % c.get("unchecked", 0))
        for k, v in sorted(c.items()):
            if k != "unchecked":
                print("%s=%d" % (k, v))
        raise SystemExit(0 if c.get("unchecked", 0) == 0 else 2)
    elif args.cmd == "drive":
        lines = drive(args.session, args.limit)
        print("\n".join(lines))
        raise SystemExit(0 if lines[0] == "STATE=L1_CLOSED" else 2)
    elif args.cmd == "radius":
        for r in explosion_radius(args.session):
            print("%d\t%s\t%s" % (r["count"], r["reason"], ",".join(r["cards"])))
    elif args.cmd == "retract":
        if not args.fact:
            raise SystemExit("FATAL: retract 需要 --fact <fact_id>")
        found, reopened = retract(args.session, args.fact)
        if not found:
            raise SystemExit("FATAL: fact_id 不存在于 facts.tsv：%s" % args.fact)
        print("RETRACTED=%s" % args.fact)
        print("REOPENED=%d" % len(reopened))
        for cid in reopened:
            print("CARD\t%s" % cid)
    elif args.cmd == "final-status":
        result = final_status(args.session)
        print(result)
        raise SystemExit(0 if result == "COMPLETED_VERIFIED" else 1)
    else:
        for c in next_wu(args.session, args.limit):
            print(c["card_id"], c.get("sink_type", ""), sep="\t")


if __name__ == "__main__":
    main()
