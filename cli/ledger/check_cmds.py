# -*- coding: utf-8 -*-
"""tanyin ledger 校验命令（批次 1 T8/T11）——契约：02a §3（第 31-36 节）＋终审补全
＋九门断言四条（ledger-scope-coverage/ledger-tree-check/ledger-replay-summary/
ledger-terminal-gate，02a 终审补全节【推导转正】）。

清单=契约 02 校验类 10 条去掉 validate/verify-chain（core 内建）。
输出=PASS/FAIL＋原因清单（top-N），exit 0/1；set-replay-state 具写语义
（落账命令归校验组，02 §3 行 6）拒收=stderr 单行 REJECT＋exit 1；
用法/环境错误 exit 2。参数本批仅 --key=value／旗标。
"""
import math, os, re   # datetime 退役（G-23 批次5 T4：_now() 墙钟删除，时间戳一律参数）

from . import core
from . import state_md
from .norm import normalize_artifact, artifact_hashes as _norm_hashes  # norm 轨单源（评审 C-1）
from .schemas import TABLES
from .query_cmds import (TAB, UsageError, parse_kv, usage_guard, _idx, _cell,
                         latest_intents, latest_matrix, latest_by, unconsumed_facts,
                         matrix_gap_cells, budget_exhausted)

REPLAY_STATES = ("VERIFIED", "REPAIRED", "REJECTED")
REPLAY_EVENT = re.compile(r"^replay:((?:EV|FD)-[^:\s]+):(VERIFIED|REPAIRED|REJECTED)(?:\s.*)?$")
MAX_RETRY = 2          # §5.2 back_edges max_retry=2
BATCH_SET_CELLS = 5    # 【推导】批量置态告警阈值：单 intent 置态格数>5 且超其 fact 数
DEFAULT_SAMPLE = 0.2   # §5.2 常量 p4_sample_ratio=0.2


def _chain_fail(s):
    ok, bad = s.verify_chain()
    return None if ok else "timeline 断链于第 %d 行" % bad


# ---------------------------------------------------------------- hash-recheck

# normalize_artifact：自 .norm 导入 re-export（既有引用兼容；实现单源=ledger/norm.py，
# 规则冻结见其模块 docstring——批次 4 评审 C-1 前此处为写/查分叉的查侧副本）


def artifact_hashes(path):
    """E-index content_hash 双轨：raw=原始字节 sha256；norm=归一化后 sha256
    （norm 单源=ledger/norm.py——add-evidence 落账与 hash-recheck 重算同款）。"""
    return _norm_hashes(open(path, "rb").read())


def h_hash_recheck(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("hash-recheck 无参数")
    s = core.Session(goal_dir)
    errs = []
    chain_err = _chain_fail(s)  # 终审补全 2：timeline 全链重算
    if chain_err:
        errs.append(chain_err)
    checked = skipped = 0
    for r in s.rows("E-index.tsv"):
        ev_id = _cell(r, "E-index.tsv", "id")
        path = _cell(r, "E-index.tsv", "artifact_path")
        if not path.strip():
            skipped += 1  # 无工件行跳过（夹具形态：工件外置可选）
            continue
        full = path if os.path.isabs(path) else os.path.join(goal_dir, path)
        if not os.path.isfile(full):
            errs.append("%s\tartifact_path 工件缺失:%s" % (ev_id, path))
            continue
        raw, norm = artifact_hashes(full)
        for col, got in (("content_hash_raw", raw), ("content_hash_norm", norm)):
            if _cell(r, "E-index.tsv", col) and _cell(r, "E-index.tsv", col) != got:
                errs.append("%s\t%s 失配" % (ev_id, col))
        checked += 1
    if errs:
        print("FAIL")
        for e in errs[:20]:
            print(e)
        return 1
    print("PASS\tchain=ok\tev_checked=%d\tev_skipped=%d" % (checked, skipped))
    return 0


# ---------------------------------------------------------------- matrix-audit

def h_matrix_audit(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"sample-ratio"}:
        raise UsageError("matrix-audit [--sample-ratio=<0-1>]")
    ratio = DEFAULT_SAMPLE
    if "sample-ratio" in args:
        try:
            ratio = float(args["sample-ratio"])
        except ValueError:
            raise UsageError("--sample-ratio 需浮点")
        if not 0 < ratio <= 1:
            raise UsageError("--sample-ratio 需 (0,1]")
    s = core.Session(goal_dir)
    latest = latest_matrix(s)
    # 抽查对象：state∈{-,!} 格（P4 抽查，§5.2）；抽样确定：排序后等距取样【推导】
    pop = [r for _, r in sorted(latest.items())
           if _cell(r, "matrix.tsv", "state") in ("-", "!")]
    n_sample = math.ceil(ratio * len(pop))
    step = max(1, len(pop) // n_sample) if n_sample else 1
    sampled = pop[::step][:n_sample] if n_sample else []
    fails = []
    for r in sampled:
        if not _cell(r, "matrix.tsv", "reason").strip():
            fails.append([_cell(r, "matrix.tsv", f)
                          for f in ("attack_surface", "vuln_class", "state", "reason")]
                         + ["-/! 格 reason 强制（02a 第 12 节）"])
    # 告警：批量置态与 fact 密度不符（§8.3 注入防护④）【推导】
    cells_by_intent = {}
    for r in latest.values():
        iid = _cell(r, "matrix.tsv", "intent_id")
        if iid.strip() and _cell(r, "matrix.tsv", "state").strip():
            cells_by_intent[iid] = cells_by_intent.get(iid, 0) + 1
    facts_by_intent = {}
    for r in s.rows("facts.tsv"):
        iid = _cell(r, "facts.tsv", "intent_id")
        facts_by_intent[iid] = facts_by_intent.get(iid, 0) + 1
    warnings = []
    for iid in sorted(cells_by_intent):
        n_cells = cells_by_intent[iid]
        if n_cells > BATCH_SET_CELLS and n_cells > facts_by_intent.get(iid, 0):
            warnings.append([iid, "置态格=%d 超阈值 %d 且超其 fact 数 %d"
                             % (n_cells, BATCH_SET_CELLS, facts_by_intent.get(iid, 0))])
    if fails or warnings:
        print("FAIL")
        for f in fails[:20]:
            print(TAB.join(f))
        for w in warnings[:20]:
            print("告警:" + w[0] + TAB + w[1])
        return 1
    print("PASS\tsampled=%d\twarnings=0" % len(sampled))
    return 0


# ---------------------------------------------------------------- state-rebuild

def h_state_rebuild(goal_dir, rest):
    """v2 对账（批次 3 T5）：链一致 + 固定段键齐/枚举合法/行数≤200（parse_state）+
    revision==timeline 行数（既有口径）+ snapshot 与账本重算一致（新增——对账实质）。
    输出首行 PASS\trevision=<n> 冻结不变（41 面）；追加信息一律第二行。
    FAIL 提示统一指向 tanyin-phases rebuild-state 对账重建（撕裂态 B/C 的恢复通道）。"""
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("state-rebuild 无参数")
    s = core.Session(goal_dir)
    chain_err = _chain_fail(s)
    if chain_err:
        print("FAIL")
        print(chain_err)
        return 1
    revision = len(s.rows("timeline.tsv"))
    st_path = os.path.join(goal_dir, "state.md")
    if not os.path.isfile(st_path):
        # 撕裂态 C（state.md 缺失）不是错误：账本为第一事实源，可 rebuild-state 重建
        print("PASS\trevision=%d" % revision)
        print("state.md=absent（tanyin-phases rebuild-state 可重建）")
        return 0
    fields, handoff, errs = state_md.parse_state(st_path)
    if errs or not fields:
        print("FAIL")
        print("state.md 损坏/空文件（tanyin-phases rebuild-state 对账重建）"
              if not errs else errs[0] + "（tanyin-phases rebuild-state 对账重建）")
        return 1
    if int(fields["revision"]) != revision:
        print("FAIL")
        print("state.md revision=%s 与账本重建 revision=%d 不一致（tanyin-phases rebuild-state 对账重建）"
              % (fields["revision"], revision))
        return 1
    expect_snap = state_md.snapshot_from_session(s)
    if fields["snapshot"] != expect_snap:
        print("FAIL")
        print("snapshot 漂移: state=%r 账本重算=%r（tanyin-phases rebuild-state 对账重建）"
              % (fields["snapshot"], expect_snap))
        return 1
    print("PASS\trevision=%d" % revision)
    print("state.md v2 对账一致 session=%s phase=%s" % (fields["session"], fields["phase"]))
    return 0


# ------------------------------------------------------------- set-replay-state

_EXPLOIT_MAP = {"VERIFIED": "verified", "REPAIRED": "verified", "REJECTED": "suspected"}
# 【推导】REPAIRED=修复 POC 后重放通过→verified；REJECTED→suspected（降 C3 风险线索，
# 非 ruled_out——ruled_out 配 ➖🛑，见完工报告探知项）


def _append_timeline(s, goal_dir, event, ts, actor="CLI", phase="P4", revert=""):
    # G-23 转正（批次5 T4）：ts 必填位置参数——墙钟缺省通道退役，时间戳一律来自命令参数
    rows = [list(r) for r in s.rows("timeline.tsv")]
    prev = rows[-1][_idx("timeline.tsv", "hash")] if rows else core.GENESIS
    wo = [ts, actor, phase, event, revert, prev, "2"]
    h = core.row_hash(prev, wo)
    rows.append([ts, actor, phase, event, revert, prev, h, "2"])
    core.write_tsv(os.path.join(goal_dir, "timeline.tsv"), rows)
    s.data["timeline.tsv"] = rows
    return rows[-1]


def h_set_replay_state(goal_dir, rest):
    import sys
    args, pos = parse_kv(rest)
    if pos or set(args) - {"id", "state", "note", "timestamp", "manual"} \
            or "id" not in args or "state" not in args \
            or not args.get("timestamp"):
        # G-23 转正（批次5 T4）：--timestamp 必填（缺/空=用法错误 exit 2），墙钟退役
        # P0 加固（2026-10-10 会诊①）：--manual=1 显式人工通道（无探针实证时的
        # 唯一放行路，事件带 note=manual 标记供 settle/报告披露）
        raise UsageError("set-replay-state --id=<EV|FD id> --state=<三态> "
                         "--timestamp=ISO8601 [--note=<附注>] [--manual=1]")
    # 批次 7 评审收尾 I-3（R-T2-2 遗留收口）：用法校验先行于锁（UsageError 路径
    # 零持锁）；goal 锁包「读账→timeline 落行→findings 联动写回」全程（filelock
    # 单源，registry._locked 同形）——读写双态同入口不动契约面，直写面闭死。
    from .filelock import goal_lock
    with goal_lock(goal_dir):
        return _set_replay_state_locked(goal_dir, args)


def _set_replay_state_locked(goal_dir, args):
    import sys
    ts = args["timestamp"]
    rid, state = args["id"], args["state"]
    s = core.Session(goal_dir)

    def reject(why):
        sys.stderr.write("REJECT\tset-replay-state\t%s\n" % why)
        return 1

    if state not in REPLAY_STATES:
        return reject("state∉{VERIFIED,REPAIRED,REJECTED}")
    target_fd = None
    if rid.startswith("FD-"):
        if rid not in {k[0] for k in latest_by(s.rows("findings.tsv"),
                                               "findings.tsv", ["id"])}:
            return reject("--id 引用闭合失败（findings 无此行）")
        target_fd = rid
    elif rid.startswith("EV-"):
        if rid not in {r[0] for r in s.rows("E-index.tsv")}:
            return reject("--id 引用闭合失败（E-index 无此行）")
        for r in s.rows("E-index.tsv"):
            if r[0] == rid:
                target_fd = _cell(r, "E-index.tsv", "linked_finding") or None
                break
    else:
        return reject("--id 须为 EV-/FD- 引用")
    retries = sum(1 for r in s.rows("timeline.tsv")
                  if REPLAY_EVENT.match(r[_idx("timeline.tsv", "event")])
                  and REPLAY_EVENT.match(r[_idx("timeline.tsv", "event")]).group(1) == rid
                  and REPLAY_EVENT.match(r[_idx("timeline.tsv", "event")]).group(2) == "REPAIRED")
    if state == "REPAIRED" and retries >= MAX_RETRY:
        return reject("REPAIRED 重试计数 %d≥max_retry=%d" % (retries, MAX_RETRY))
    # 缝⑪/G-52（批次 9 三轮战复核）：P4 门拦下 not-reproduced 后，VERIFIED/REPAIRED
    # 不得越过复放实证改判——该 id 最新 replay-probe 裁决=not-reproduced 且无更晚
    # reproduced 行 ⇒ 拒（--manual 也不能翻案：事实矛盾须补 reproduced 探针）。
    # P0 加固（2026-10-10 九维专家会诊·诚实性缺口①）：无探针行不再静默放行——
    # VERIFIED/REPAIRED 须同 id（FD 则其挂接 EV 任一）存在 replay-probe
    # reproduced 实证；无实证仅 --manual=1 显式人工通道可过，事件带 manual 标记。
    manual = args.get("manual") == "1"
    if state in ("VERIFIED", "REPAIRED"):
        import re as _re
        pat = _re.compile(r"replay-probe (\S+) verdict=(\S+)")
        if rid.startswith("EV-"):
            probe_ids = {rid}
        else:
            probe_ids = {r[0] for r in s.rows("E-index.tsv")
                         if (_cell(r, "E-index.tsv", "linked_finding") or "") == rid}
        last_by_id = {}
        for r in s.rows("timeline.tsv"):
            m = pat.search(r[_idx("timeline.tsv", "event")])
            if m and m.group(1) in probe_ids:
                last_by_id[m.group(1)] = m.group(2)
        reproduced = [i for i, v in last_by_id.items() if v == "reproduced"]
        # REPAIRED 语义=修复后重放——env-diff 探针（环境差异非失败）亦算实证
        acceptable = ([i for i, v in last_by_id.items()
                       if v in ("reproduced", "env-diff")]
                      if state == "REPAIRED" else reproduced)
        blocked = [i for i, v in last_by_id.items() if v == "not-reproduced"]
        if blocked:
            return reject("最新 replay-probe 裁决=not-reproduced（%s）：VERIFIED/REPAIRED "
                          "须先补 reproduced 探针——--manual 不能翻事实矛盾"
                          % ",".join(sorted(blocked)))
        if not acceptable and not manual:
            return reject("无 replay-probe reproduced 实证：VERIFIED/REPAIRED 须先实放"
                          "（或 --manual=1 显式人工通道，事件将带 manual 标记）")

    note_parts = []
    if manual:
        note_parts.append("manual")
    if args.get("note"):
        note_parts.append(args["note"])
    ev = "replay:%s:%s" % (rid, state) + \
        ((" note=" + ";".join(note_parts)) if note_parts else "")
    tl_row = _append_timeline(s, goal_dir, ev, ts)
    fd_row = None
    if target_fd:
        rows = [list(r) for r in s.rows("findings.tsv")]
        src = None
        for r in rows:
            if r[0] == target_fd:
                src = list(r)
        if src is None:
            return reject("linked_finding 引用闭合失败（findings 无此行）")
        new = list(src)
        new[_idx("findings.tsv", "exploitation_status")] = _EXPLOIT_MAP[state]
        if state == "REJECTED" and new[_idx("findings.tsv", "confidence")] in ("C1", "C2"):
            new[_idx("findings.tsv", "confidence")] = "C3"  # REJECTED 降 C3（§4.7）
        new[_idx("findings.tsv", "created")] = ts   # G-23：联动行 created=参数（墙钟退役）
        rows.append(new)
        core.write_tsv(os.path.join(goal_dir, "findings.tsv"), rows)
        fd_row = new
    print("OK\treplay:%s:%s" % (rid, state))
    print(TAB.join(tl_row))
    if fd_row:
        print(TAB.join(fd_row))
    return 0


# ------------------------------------------------------ 九门断言四条（02a 终审）

def h_scope_coverage(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("ledger-scope-coverage 无参数")
    s = core.Session(goal_dir)
    errs = []
    if not s.rows("goals.tsv"):
        errs.append("账本缺失：无 goals 行")
    chain_err = _chain_fail(s)
    if chain_err:
        errs.append(chain_err)
    kinds = {_cell(r, "scope.tsv", "kind") for r in s.rows("scope.tsv")}
    for need in ("include", "exclude", "oob"):  # 02 §1 行 2：齐备由本断言检查
        if need not in kinds:
            errs.append("scope 缺 kind=%s 行" % need)
    if errs:
        print("FAIL")
        for e in errs:
            print(e)
        return 1
    print("PASS\tscope 覆盖齐备：include/exclude/oob 各≥1")
    return 0


def h_tree_check(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("ledger-tree-check 无参数")
    s = core.Session(goal_dir)
    chain_err = _chain_fail(s)
    if chain_err:
        print("FAIL")
        print(chain_err)
        return 1
    assets = s.rows("assets.tsv")
    ids = {r[0]: r for r in assets}
    parent_of = {}   # 【推导】parent 边方向：source=子资产，target=父资产
    errs = []
    for r in s.rows("edges.tsv"):
        if _cell(r, "edges.tsv", "kind") != "parent":
            continue
        child, parent = _cell(r, "edges.tsv", "source_id"), _cell(r, "edges.tsv", "target_id")
        if child not in ids or parent not in ids:
            errs.append("%s parent 边引用不存在资产 %s->%s" % (r[0], child, parent))
            continue
        if child == parent:
            errs.append("%s parent 边自指 %s" % (r[0], child))
            continue
        if child in parent_of:
            errs.append("%s 多父（%s 与 %s）" % (child, parent_of[child], parent))
            continue
        parent_of[child] = parent
    # 环检测（森林性质）
    for a in sorted(ids):
        seen, cur = set(), a
        while cur in parent_of:
            if cur in seen:
                errs.append("资产树成环：%s" % a)
                break
            seen.add(cur)
            cur = parent_of[cur]
    # 【推导】根类型=root-domain/ip；派生类型（subdomain/service/app/endpoint/
    # source-code/pivot/foothold）须挂 parent 边
    for r in sorted(assets, key=lambda x: x[0]):
        if _cell(r, "assets.tsv", "type") not in ("root-domain", "ip") \
                and r[0] not in parent_of:
            errs.append("%s(type=%s) 缺 parent 边"
                        % (r[0], _cell(r, "assets.tsv", "type")))
    if errs:
        print("FAIL")
        for e in errs[:20]:
            print(e)
        return 1
    print("PASS\t资产树完整：%d 资产/%d parent 边" % (len(assets), len(parent_of)))
    return 0


def h_anchor(goal_dir, rest):
    """P0 加固（2026-10-10 会诊③·审计缺口①）：链头外部锚定。

    把 goal 目录账本面（*.tsv）git commit（无仓库则 init），消息携带行数+链头；
    --remote/TANYIN_ANCHOR_REMOTE 在场则 push（尽力而为）。无声改账从此须
    重写已推送 git 历史。门过自动锚=TANYIN_ANCHOR_AUTO=1（engine 侧钩子）。"""
    import subprocess as _sp
    args, pos = parse_kv(rest)
    if pos or set(args) - {"timestamp", "remote", "note"}:
        raise UsageError("anchor [--timestamp=ISO8601] [--remote=URL] [--note=<附注>]")
    from .filelock import goal_lock
    with goal_lock(goal_dir):
        s = core.Session(goal_dir)
        rows = s.rows("timeline.tsv")
        head = rows[-1][_idx("timeline.tsv", "hash")] if rows else core.GENESIS
        msg = "anchor rows=%d head=%s%s%s" % (
            len(rows), head[:16],
            (" ts=" + args["timestamp"]) if args.get("timestamp") else "",
            (" note=" + args["note"]) if args.get("note") else "")

        def git(*a):
            return _sp.run(["git"] + list(a), cwd=goal_dir,
                           capture_output=True, text=True)

        if not os.path.isdir(os.path.join(goal_dir, ".git")):
            r = git("init", "-q")
            if r.returncode != 0:
                print("FAIL git init: " + (r.stderr or "").strip()[:120])
                return 1
        git("add", "*.tsv")
        ok = git("commit", "-q", "-m", msg, "--allow-empty").returncode == 0
        remote = args.get("remote") or os.environ.get("TANYIN_ANCHOR_REMOTE", "")
        pushed = False
        if remote:
            git("remote", "remove", "anchor")
            git("remote", "add", "anchor", remote)
            pushed = git("push", "-q", "anchor", "HEAD").returncode == 0
        sha = git("rev-parse", "--short", "HEAD").stdout.strip()
        print("PASS\tanchor commit=%s rows=%d head=%s%s"
              % (sha, len(rows), head[:16],
                 "\tpush=" + ("ok" if pushed else "FAIL") if remote else ""))
        return 0 if ok else 1


def h_replay_summary(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("ledger-replay-summary 无参数")
    s = core.Session(goal_dir)
    counts = {st: 0 for st in REPLAY_STATES}
    replayed = set()
    for r in s.rows("timeline.tsv"):
        m = REPLAY_EVENT.match(r[_idx("timeline.tsv", "event")])
        if m:
            counts[m.group(2)] += 1
            replayed.add(m.group(1))
    pending = []
    total_c12 = 0
    covered_evs = 0
    total_evs = 0
    for key, r in sorted(latest_by(s.rows("findings.tsv"), "findings.tsv",
                                   ["id"]).items()):
        fid = key[0]  # latest_by 键为元组
        if _cell(r, "findings.tsv", "status") == "superseded":
            continue
        if _cell(r, "findings.tsv", "confidence") not in ("C1", "C2"):
            continue  # 【推导】重放义务=C1/C2 实证档（VERIFIED 才维持 C1）
        evs = {x for x in _cell(r, "findings.tsv", "evidence_ids").split(";") if x}
        linked = {e[0] for e in s.rows("E-index.tsv")
                  if _cell(e, "E-index.tsv", "linked_finding") == fid}
        all_evs = evs | linked
        total_c12 += 1
        total_evs += len(all_evs)
        covered_evs += len(all_evs & replayed)
        if fid not in replayed and not (evs & replayed) and not (linked & replayed):
            pending.append([fid, _cell(r, "findings.tsv", "title")])
        else:
            # P0 加固（2026-10-10 会诊④/RT-0023 32/54 洞）：C1/C2 的全部证据
            # 须终态（VERIFIED/REPAIRED/REJECTED 任一在案）——"任一已重放"
            # 不再放行出 P4。
            uncovered = sorted(all_evs - replayed)
            if uncovered:
                pending.append([fid, "%s｜EV未终态:%s"
                                % (_cell(r, "findings.tsv", "title"),
                                   ",".join(uncovered[:5]))])
    if pending:
        print("FAIL")
        for p in pending[:20]:
            print(TAB.join(p) + TAB + "待重放")
        return 1
    cov = ("%.0f%%" % (100.0 * covered_evs / total_evs)) if total_evs else "n/a"
    print("PASS\tverified=%d\trepaired=%d\trejected=%d\tpending=0"
          "\tc12_findings=%d\tev_coverage=%s"
          % (counts["VERIFIED"], counts["REPAIRED"], counts["REJECTED"],
             total_c12, cov))
    return 0


def h_terminal_gate(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or args:
        raise UsageError("ledger-terminal-gate 无参数")
    s = core.Session(goal_dir)
    errs = []
    if not s.rows("goals.tsv"):
        errs.append("账本缺失：无 goals 行")
    chain_err = _chain_fail(s)
    if chain_err:
        errs.append(chain_err)
    gaps = matrix_gap_cells(s)  # §3.10：空=未检查，空必须消灭（终态门禁）
    for r in gaps:
        errs.append("空格未清零：%s/%s" % (_cell(r, "matrix.tsv", "attack_surface"),
                                          _cell(r, "matrix.tsv", "vuln_class")))
    # 锚点冻结断言=「freeze 时在场行」（批次 7 T16 工具缝①）：freeze 后 matrix-set 追加行
    # frozen_at 恒空，latest 行取锚使 P3 置格会话 P5 门不可达——改为全表任意 frozen_at 非空行。
    if s.rows("matrix.tsv") and not any(
            _cell(r, "matrix.tsv", "frozen_at").strip() for r in s.rows("matrix.tsv")):
        errs.append("锚点未冻结（matrix 无 frozen_at 非空行）")
    if errs:
        print("FAIL")
        for e in errs[:20]:
            print(e)
        return 1
    print("PASS\t终态门禁：空格=0，锚点已冻结")
    return 0


HANDLERS = {name: usage_guard(fn) for name, fn in {
    "hash-recheck": h_hash_recheck,
    "matrix-audit": h_matrix_audit,
    "state-rebuild": h_state_rebuild,
    "set-replay-state": h_set_replay_state,
    "anchor": h_anchor,
    "ledger-scope-coverage": h_scope_coverage,
    "ledger-tree-check": h_tree_check,
    "ledger-replay-summary": h_replay_summary,
    "ledger-terminal-gate": h_terminal_gate,
}.items()}
