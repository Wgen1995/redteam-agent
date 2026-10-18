# -*- coding: utf-8 -*-
"""功能26 报告补件一/三：证据角色+证据集版本+manifest 过期检测（报告舰领地）。

设计稿=docs/design/2026-10-20-report-upgrade-design.md（ARTEX 证据中心工程吸收）：
- 证据绑定带**角色**（proof 漏洞证明/baseline 正常对照/verification 补充验证/
  supporting 辅助）与**顺序**——基线角色自账本零新事实投影：evidence_ids→proof、
  control_evidence_ids→baseline（对照证据即正常对照，无第二事实源）。
- finding 证据集带**版本号**：任何绑定增删改=+1。两个事实源各记各的账——
  ①findings.tsv 修订行（绑定投影逐行比对，变化=+1）；②report/evidence-bindings.tsv
  绑定日志（bind/rebind/unbind 各+1，append-only，esc 转义同账本口径）。
  入库路径（add-finding/add-evidence）零触碰——哨兵舰领地不动，报告侧只读投影+自管日志。
- 过期拒写（机械门，不靠自觉）：render/write_all 携带 evidence_version 与账本当前
  不符=拒写（「证据已变化,待重写」）；write_all 落 report-manifest（各 active finding
  的 evidence_version 快照），下次渲染前比对——漂移=StaleEvidenceError（待重写清单
  载哪几个 finding 的证据动了），不渲染半新半旧报告。
- 恢复路径：rewrite_evidence——逐 active FD 重渲染 draft+manifest 快照刷新
  （报告员被打回≤2 轮内完成重读重写；帽=兵种卡纪律，机械面在此）。

纪律：纯 stdlib+账本单源；零墙钟（ts 全显式传入）；Python 3.9。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger.core import Session, esc, unesc  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

TOOL_NAME = "tanyin-report"
ROLES = ("proof", "baseline", "verification", "supporting")
BINDINGS_NAME = "evidence-bindings.tsv"      # 绑定日志（report/ 下，报告侧自管）
MANIFEST_NAME = "report-manifest.json"       # evidence_version 快照（write_all 落）
STALE_WHY = "证据已变化,待重写"
# 日志列（无表头同账本口径；列序=本常量单源）
JOURNAL_COLUMNS = ("finding_id", "evidence_id", "role", "ord", "action",
                   "version", "timestamp")
_ACTIONS = ("bind", "unbind")


class StaleEvidenceError(Exception):
    """证据集版本漂移——渲染/签发拒写（不产半新半旧报告）。

    drift=[{finding, manifest_version, current_version}]（待重写清单数据面）。
    """

    def __init__(self, drift):
        self.drift = drift
        super(StaleEvidenceError, self).__init__(
            STALE_WHY + ": " + ",".join(self.stale_ids()))

    def stale_ids(self):
        return [d["finding"] for d in self.drift]


def _cell(t, r, col):
    return r[TABLES[t].index(col)]


def _fd_rows(s, fd_id):
    return [r for r in s.rows("findings.tsv") if _cell("findings.tsv", r, "id") == fd_id]


def _base_state(fd_row):
    """findings 行→基线绑定投影（零新事实：evidence_ids→proof/control→baseline）。"""
    out = []
    for col, role in (("evidence_ids", "proof"), ("control_evidence_ids", "baseline")):
        out += [(x, role) for x in _cell("findings.tsv", fd_row, col).split(";") if x]
    return tuple(out)


# ---------------------------------------------------------------- 日志读写

def _journal_path(goal_dir):
    return os.path.join(goal_dir, "report", BINDINGS_NAME)


def _journal(goal_dir):
    """绑定日志行（dict 列表；缺件=空；文件序=事件序）。"""
    p = _journal_path(goal_dir)
    if not os.path.isfile(p):
        return []
    rows = []
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln.strip():
                continue
            vals = [unesc(c) for c in ln.split("\t")]
            vals += [""] * (len(JOURNAL_COLUMNS) - len(vals))
            rows.append(dict(zip(JOURNAL_COLUMNS, vals)))
    return rows


def append_binding(goal_dir, finding_id, evidence_id, role="", order=None,
                   action="bind", timestamp=""):
    """绑定动作入日志；返回动作后版本。角色词表外/引用不闭合=fail-closed ValueError。

    bind=新增或改绑（role+order 全量入档）；unbind=解绑（role 空档）。每次动作
    版本+1（「绑定增删改=+1」机械计数，不判内容是否实质变化）。
    """
    if action not in _ACTIONS:
        raise ValueError("action 不在 {bind,unbind}: " + action)
    s = Session(goal_dir)
    if not _fd_rows(s, finding_id):
        raise ValueError("finding 引用闭合失败: " + finding_id)
    ev_ids = {r[0] for r in s.rows("E-index.tsv")}
    if evidence_id not in ev_ids:
        raise ValueError("evidence 引用闭合失败: " + evidence_id)
    if action == "bind":
        if role not in ROLES:
            raise ValueError("role 不在 %s: %s" % (list(ROLES), role))
        if order is not None and int(order) < 1:
            raise ValueError("order 须≥1: %s" % order)
    version = evidence_version(goal_dir, finding_id) + 1
    p = _journal_path(goal_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    row = [finding_id, evidence_id, role if action == "bind" else "",
           str(order) if order else "", action, str(version), timestamp]
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(esc(c) for c in row) + "\n")
    return version


# ---------------------------------------------------------------- 版本与绑定集

def evidence_version(goal_dir, fd_id):
    """finding 证据集当前版本=1+findings 修订行绑定变化数+日志行数（确定性计数）。"""
    s = Session(goal_dir)
    version, prev = 1, None
    for r in _fd_rows(s, fd_id):
        cur = _base_state(r)
        if prev is not None and cur != prev:
            version += 1
        prev = cur
    return version + sum(1 for j in _journal(goal_dir) if j["finding_id"] == fd_id)


def bindings(goal_dir, fd_id):
    """当前绑定集（带角色与顺序）：findings 末行基线投影+日志折叠（后写覆盖先写）。

    返回 [{evidence_id, role, order}]，按（order, evidence_id）稳定排序。
    """
    s = Session(goal_dir)
    rows = _fd_rows(s, fd_id)
    if not rows:
        return []
    items = {}
    for i, (ev, role) in enumerate(_base_state(rows[-1]), 1):
        items[ev] = {"role": role, "order": i}
    for j in _journal(goal_dir):
        if j["finding_id"] != fd_id:
            continue
        ev = j["evidence_id"]
        if j["action"] == "unbind":
            items.pop(ev, None)
            continue
        order = int(j["ord"]) if j["ord"].strip() else (
            items.get(ev, {}).get("order") or len(items) + 1)
        items[ev] = {"role": j["role"], "order": order}
    return [{"evidence_id": ev, "role": it["role"], "order": it["order"]}
            for ev, it in sorted(items.items(), key=lambda kv: (kv[1]["order"], kv[0]))]


def active_version_map(goal_dir):
    """报告面（active FD 集）各 finding 的 evidence_version 快照字典。"""
    from ledger import report_render   # 惰性导入（report_render 仅函数内反向引用）
    s = Session(goal_dir)
    return {fid: evidence_version(goal_dir, fid)
            for fid in report_render.active_fd_ids(s)}


# ---------------------------------------------------------------- manifest 过期检测

def _manifest_path(goal_dir):
    return os.path.join(goal_dir, "report", MANIFEST_NAME)


def read_manifest(goal_dir):
    """读 manifest；缺件=None；损坏=json 解析错向上抛（fail-closed 不静默重置）。"""
    p = _manifest_path(goal_dir)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_manifest(goal_dir, ts=""):
    """落 manifest（active 集 evidence_version 快照）；返回快照文档。"""
    snap = {"schema_version": 1, "tool": {"name": TOOL_NAME}, "ts": ts,
            "evidence_versions": active_version_map(goal_dir)}
    p = _manifest_path(goal_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(snap, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
    return snap


def manifest_drift(goal_dir):
    """manifest 快照 vs 账本当前版本。返回 (drift, manifest)。

    drift=[{finding, manifest_version, current_version}]（快照在档且版本不符的
    active finding；finding 已离场=current_version=None 同计漂移——报告面删证据
    也是变化）。无 manifest/无漂移=空清单。
    """
    m = read_manifest(goal_dir)
    if not m:
        return [], None
    cur = active_version_map(goal_dir)
    drift = []
    for fid, mv in sorted((m.get("evidence_versions") or {}).items()):
        if cur.get(fid) != mv:
            drift.append({"finding": fid, "manifest_version": mv,
                          "current_version": cur.get(fid)})
    return drift, m


def rewrite_evidence(goal_dir, ts=""):
    """恢复路径：逐 active FD 重渲染 draft+manifest 快照刷新。

    待重写清单的消费端——证据变化后由报告员/人工执行（≤2 轮帽内），完成后
    write_all/sign 复绿。返回 (rc, detail)：rc=0 detail=重渲染 FD id 清单。
    """
    from ledger import report_render
    s = Session(goal_dir)
    fids = report_render.active_fd_ids(s)
    draft_dir = os.path.join(goal_dir, "report", "draft")
    os.makedirs(draft_dir, exist_ok=True)
    for fid in fids:
        rc, md = report_render.render_fd(goal_dir, fid)
        if rc != 0:
            return 1, "重写 FAIL(%s): %s" % (fid, md)
        with open(os.path.join(draft_dir, fid + ".md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(md)
    write_manifest(goal_dir, ts)
    return 0, fids
