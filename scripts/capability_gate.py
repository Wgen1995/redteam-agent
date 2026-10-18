#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_gate · 评测棘轮（演进飞轮第 4 齿·宪法#43 核心件——误报漏报率机器）。

设计权威 docs/design/evolution-flywheel-v1.md：一切能力件变更（技法卡/避坑卡/
提示词文件/工具卡）合并前必须过 GT-scorecard 评测增量——召回率/误报率不得
回退，回退超阈值=拒合并。知识也有 CI，能力回归=工程回归同律（rc 契约同
契约 09 面：0=过 1=拒 2=环境）。

复用面（D2 三臂同考件，不重写评分器）：
  scorer  = tests/eval_range_recall.py（同 GT 同 scorer 口径=D2 判分核；subprocess
            实跑=scripts/battle.py cmd_settle 同法）；
  数据面  = battle 家目录（<suite>/battle-N/G-<gen>/ 会话 + <gt-dir>/<gen>.json
            GT，battle.py gt_out_path 同源布局）；
  误报面  = 活发现集内重放证伪（timeline replay:FD/EV REJECTED + replay-probe
            not-reproduced——G-52 越权改判防线同证据基，评分侧复设口径）。
  三臂位 = delta JSON 带 arm 位（本臂=tanyin；ARTEX/VulnClaw 臂属 D2 仓外
            实跑，本地夹具零外联不代跑——诚实披露不虚造）。

棘轮律：baseline 文件存上次过关聚合（collect-first 首跑入册=契约 15 M01 同
先例）；--update-baseline 只紧不松（召回率只升误报率只降，否则拒更）。

两形态：
  CLI 显式：python3 scripts/capability_gate.py --base HEAD \\
              --suite ~/.tanyin/battles --out /tmp/capability-delta.json
  git hook：pre-merge-commit/pre-push 一行挂载（本仓不强制入 .git/hooks，
            挂载示例见文末 HOOK NOTES）；--hook=单行 terse 输出，rc 同契约。

避坑卡（negative 卡型）schema 面也住本件（knowledge/ 卡型扩 negative：失败
路径/条件/出处=账本行号；cp-index 家族兼容扩列——经典六列零破，扩列四键
可选；蒸馏管线本体=W5 知识环舰，本件只留读写面 write_negative_card）。

HOOK NOTES：
  .git/hooks/pre-merge-commit:
      #!/bin/sh
      python3 "$(git rev-parse --show-toplevel)/scripts/capability_gate.py" \\
          --hook --base HEAD "$@" || exit 1
  pre-push 同形（--base 取远端追踪支时由调用方显式传）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

EPS = 1e-9
SCORER_REL = os.path.join("tests", "eval_range_recall.py")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GateEnvError(Exception):
    """环境不可用（git 缺/套件缺/评分器不可跑）——rc2 fail-closed。"""


class SeedFrozenError(Exception):
    """种子库只读纪律（R7）：仓库 knowledge/ 拒绝写子命令。"""


# ============================================================ 避坑卡 schema ==
# knowledge/ 卡型扩 negative（设计第 2 齿：正知识+负知识双轨——避坑卡=CP 技法
# 卡家族负轨，共享 CP- 四位编号空间，物理落 knowledge/negative/（不在
# tanyin-knowledge LINT_ZONES——六类冻结面零触碰，W5 蒸馏舰后续接管正式区）。

NEGATIVE_DIR = "negative"
NEG_INDEX_NAME = "ng-index.tsv"
# cp-index.tsv 家族兼容列：前六列与 cp-index.tsv 逐名同序同义（经典读方零破），
# 扩列四键可选（缺列=空）。knowledge/cp-index.tsv 本体保持 50 行六列冻结
# （tests/test_w3_cp_ingest.py 钉）——负面轨索引落 ng-index.tsv，读取面同一家族。
CP_INDEX_BASE_COLS = ("id", "title", "source_id", "source_topic", "status", "updated")
NEG_INDEX_EXT_COLS = ("kind", "failure_path", "conditions", "ledger_ref")

NEG_FIELD_ORDER = ("id", "kind", "title", "failure_path", "conditions",
                   "ledger_ref", "vuln_class", "status", "last_verified",
                   "source_id", "applicability", "judgment", "cost_hint",
                   "source_topic")
NEG_REQUIRED = ("id", "kind", "title", "failure_path", "conditions",
                "ledger_ref", "vuln_class", "status", "last_verified")
NEG_STATUS = ("core", "learned", "demoted")
_ID_RE = re.compile(r"^CP-\d{4}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 出处=账本行号：battle-N/<表>.tsv:<行号>（物理行序=游标域，cmds.tsv 同律）
LEDGER_REF_RE = re.compile(r"^battle-\d+/[A-Za-z0-9_.\-]+\.tsv:\d+$")


def _repo_seed_root():
    """仓库种子库根=本件（scripts/capability_gate.py）上两级/knowledge。"""
    return os.path.join(REPO_ROOT, "knowledge")


def _parse_front(text):
    """front matter KV 平铺（api_v2_techniques 同款窄面；坏页=None）。"""
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    out = {}
    for ln in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", ln)
        if kv:
            out[kv.group(1)] = kv.group(2).strip()
    return out


def validate_negative_card(fm):
    """避坑卡 front matter 校验 → 问题清单（空=过）。"""
    problems = []
    for f in NEG_REQUIRED:
        if not str(fm.get(f, "")).strip():
            problems.append("缺必填字段 %s" % f)
    if fm.get("kind") and fm.get("kind") != "negative":
        problems.append("kind 须为 negative: %r" % fm.get("kind"))
    if fm.get("id") and not _ID_RE.match(str(fm.get("id"))):
        problems.append("id 须 ^CP-\d{4}$（CP 家族共享编号空间）: %r" % fm.get("id"))
    if fm.get("ledger_ref") and not LEDGER_REF_RE.match(str(fm.get("ledger_ref"))):
        problems.append("ledger_ref 须为 battle-N/<表>.tsv:<行号>（账本行号出处）: %r"
                        % fm.get("ledger_ref"))
    if fm.get("status") and fm.get("status") not in NEG_STATUS:
        problems.append("status 须 ∈%s: %r" % (str(NEG_STATUS), fm.get("status")))
    if fm.get("last_verified") and not _DATE_RE.match(str(fm.get("last_verified"))):
        problems.append("last_verified 须 ISO 日期: %r" % fm.get("last_verified"))
    if len(str(fm.get("title", ""))) > 60:
        problems.append("title 超 60 字")
    return problems


def read_index_family(path):
    """cp-index 家族读（经典六列/扩列十列两形通吃；表头驱动，缺列=空）。
    首行表头；坏行跳过；缺文件=空表。兼容律=前六列与 cp-index.tsv 同名同序。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
    except OSError:
        return []
    if not lines:
        return []
    head = lines[0].split("\t")
    out = []
    for ln in lines[1:]:
        cols = ln.split("\t")
        row = {h: (cols[i] if i < len(cols) else "") for i, h in enumerate(head)}
        if row.get("id"):
            out.append(row)
    return out


def _negative_index_path(knowledge_dir):
    return os.path.join(knowledge_dir, NEGATIVE_DIR, NEG_INDEX_NAME)


def _cp_nums(ids):
    nums = []
    for i in ids:
        m = re.match(r"^CP-(\d{4})$", str(i))
        if m:
            nums.append(int(m.group(1)))
    return nums


def next_negative_id(knowledge_dir):
    """避坑卡下一号=CP 家族编号空间跨索引连续（cp-index ∪ ng-index max+1）。"""
    nums = _cp_nums([r.get("id") for r in
                     read_index_family(os.path.join(knowledge_dir, "cp-index.tsv"))])
    nums += _cp_nums([r.get("id") for r in
                      read_index_family(_negative_index_path(knowledge_dir))])
    return "CP-%04d" % ((max(nums) + 1) if nums else 1)


def _atomic_write(path, text, suffix=".tmp"):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_negative_card(knowledge_dir, fields, body=""):
    """避坑卡写面（W5 蒸馏舰的落库通道）：卡 md + ng-index 行 upsert。
    编号缺省自动分配（CP 家族连续）；校验不过=ValueError；种子库=拒写（R7）。"""
    kd = os.path.abspath(knowledge_dir)
    if kd == os.path.abspath(_repo_seed_root()):
        raise SeedFrozenError("种子库只读纪律（R7）：仓库 knowledge/ 拒绝写子命令")
    fm = dict(fields)
    if not str(fm.get("id", "")).strip():
        fm["id"] = next_negative_id(kd)
    problems = validate_negative_card(fm)
    if problems:
        raise ValueError("避坑卡校验不过: " + "; ".join(problems))
    order = [k for k in NEG_FIELD_ORDER if str(fm.get(k, "")).strip()]
    for k in sorted(fm):
        if k not in order and str(fm.get(k, "")).strip():
            order.append(k)
    neg_dir = os.path.join(kd, NEGATIVE_DIR)
    os.makedirs(neg_dir, exist_ok=True)
    md = os.path.join(neg_dir, fm["id"] + ".md")
    _atomic_write(md, "---\n" + "".join(
        "%s: %s\n" % (k, fm[k]) for k in order) + "---\n\n" + (body or ""))
    # 索引行（前六列 cp-index 同义：updated=last_verified 确定性锚）
    base = {"id": fm["id"], "title": fm.get("title", ""),
            "source_id": fm.get("source_id", ""),
            "source_topic": fm.get("source_topic", ""),
            "status": fm.get("status", ""), "updated": fm.get("last_verified", "")}
    ext = {"kind": fm.get("kind", "negative"),
           "failure_path": fm.get("failure_path", ""),
           "conditions": fm.get("conditions", ""),
           "ledger_ref": fm.get("ledger_ref", "")}
    row = dict(base, **ext)
    idx_path = _negative_index_path(kd)
    rows = [r for r in read_index_family(idx_path) if r.get("id") != fm["id"]]
    rows.append(row)
    rows.sort(key=lambda r: r.get("id", ""))
    header = list(CP_INDEX_BASE_COLS + NEG_INDEX_EXT_COLS)
    text = "\t".join(header) + "\n" + "".join(
        "\t".join(str(r.get(c, "")) for c in header) + "\n" for r in rows)
    _atomic_write(idx_path, text)
    return md


def read_negative_cards(knowledge_dir):
    """避坑卡读面：knowledge/negative/*.md front matter（kind=negative）清单。"""
    d = os.path.join(knowledge_dir, NEGATIVE_DIR)
    try:
        names = sorted(n for n in os.listdir(d) if n.endswith(".md"))
    except OSError:
        return []
    out = []
    for name in names:
        try:
            with open(os.path.join(d, name), encoding="utf-8", errors="replace") as f:
                fm = _parse_front(f.read())
        except OSError:
            fm = None
        if fm and fm.get("kind") == "negative":
            out.append(fm)
    return out


# ============================================================ 变更检测 ==
# 能力件 pathspec（设计第 4 齿「技法卡/提示词/工具卡」三面；模型道=W5/W6 扩
# 展位不入 v1 面）：技法卡=cp-index.tsv±行+concepts/ 卡体+negative/ 避坑卡；
# 提示词文件=phases/<门>.md（战士单门单载面）+SKILL.md（总控路由）；工具卡=
# tools.lock（供应链锁）。

CAPABILITY_SPECS = (
    ("technique_cards", ("knowledge/cp-index.tsv", "knowledge/concepts",
                         "knowledge/negative")),
    ("prompt_files", ("phases", "SKILL.md")),
    ("tool_lock", ("tools.lock",)),
)


def _git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise GateEnvError("git %s 失败: %s" % (args[0], (r.stderr or "").strip()[:200]))
    return r.stdout


def detect_changes(repo, base="HEAD"):
    """base..worktree(+index+未跟踪) 对能力件 pathspec 的变更集。
    返回 {changed, surfaces:{面:[relpath]}, files:[全量排序]}——面归类单源
    CAPABILITY_SPECS；未跟踪新卡（ls-files --others）同计。"""
    surfaces = dict((name, set()) for name, _ in CAPABILITY_SPECS)
    for surface, specs in CAPABILITY_SPECS:
        for line in _git(repo, "diff", "--name-status", base, "--", *specs).splitlines():
            parts = [p for p in line.split("\t") if p]
            if parts:
                surfaces[surface].add(parts[-1])     # R100\told\tnew 取新位
        for line in _git(repo, "ls-files", "--others", "--exclude-standard",
                         "--", *specs).splitlines():
            if line.strip():
                surfaces[surface].add(line.strip())
    files = sorted(set().union(*surfaces.values())) if surfaces else []
    return {"changed": bool(files),
            "surfaces": dict((k, sorted(v)) for k, v in surfaces.items()),
            "files": files}


# ==================================================== GT-scorecard 复跑 ==

def _read_table(path):
    """账本表读 → 行集（冻结列序，无表头为主形——真实 battle 会话=schemas.py
    TABLES 列序裸行；夹具带表头形同吃：首列==列名即让行）。缺文件=空
    （降级不炸）。列位锚定见 _F*/_T* 常量组（宽度护栏在取值处）。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
    except OSError:
        return []
    rows = [ln.split("\t") for ln in lines]
    if rows and rows[0] and rows[0][0] in ("id", "timestamp", "attack_surface"):
        rows = rows[1:]
    return rows


_REPLAY_RE = re.compile(r"^replay:(\S+?):(VERIFIED|REPAIRED|REJECTED)")
_PROBE_RE = re.compile(r"replay-probe (\S+) verdict=(\S+)")

# 账本冻结列位（schemas.py TABLES 单源；真实会话无表头——列序=契约锚）：
# findings.tsv 19 列：id=0 evidence_ids=13 control_evidence_ids=14
# status=16（tests 侧 TABLES 断言钉——列位漂移=测试红）；timeline 8 列
# event=3。
_FINDINGS_W, _TIMELINE_W = 19, 8
_FI_ID, _FI_EV, _FI_CEV, _FI_STATUS = 0, 13, 14, 16
_TI_EVENT = 3


def fp_of_session(session_dir):
    """误报面（活发现集内重放证伪计数）→ (fp, active)。
    证据基=timeline 事件溯源末值（G-52 评分侧同源）：FD 最新 replay=REJECTED，
    或其任一 EV 被 replay-probe not-reproduced（未翻案）/EV REJECTED 拖累
    ——同一发现多信号不双计；active=status∈{"",active} 末值行集。"""
    frows = _read_table(os.path.join(session_dir, "findings.tsv"))
    if not frows:
        return 0, 0
    latest = {}
    for r in frows:
        if len(r) == _FINDINGS_W:
            latest[r[_FI_ID]] = r
    active = [r for r in latest.values() if r[_FI_STATUS] in ("", "active")]
    trows = _read_table(os.path.join(session_dir, "timeline.tsv"))
    state, probe_last = {}, {}
    for r in trows:
        if len(r) != _TIMELINE_W:
            continue
        ev = r[_TI_EVENT]
        m = _REPLAY_RE.match(ev)
        if m:
            state[m.group(1)] = m.group(2)
        m2 = _PROBE_RE.search(ev)
        if m2:
            probe_last[m2.group(1)] = m2.group(2)
    blocked = {i for i, v in probe_last.items() if v == "not-reproduced"}
    blocked |= {i for i, v in state.items()
                if i.startswith("EV-") and v == "REJECTED"}
    fp = 0
    for r in active:
        fid = r[_FI_ID]
        evs = [x for x in r[_FI_EV].split(";") if x]
        evs += [x for x in r[_FI_CEV].split(";") if x]
        if state.get(fid) == "REJECTED" or any(e in blocked for e in evs):
            fp += 1
    return fp, len(active)


_BATTLE_RE = re.compile(r"^battle-(\d+)$")
_GEN_RE = re.compile(r"^G-[A-Za-z0-9\-]*\d+")
_RECALL_OUT = re.compile(r"recall=([0-9.]+) \((\d+)/(\d+)\)")


def _gen_of(home):
    """battle 目录内 G-* 会话目录：主代优先（(首数字,名) 字典序首位——
    "G-r30" 排在 "G-r30.bak-preReplay" 前，.bak/.corrupt 备份族不夺位）；
    缺=None。"""
    try:
        names = [n for n in os.listdir(home) if n.startswith("G-")
                 and os.path.isdir(os.path.join(home, n))]
    except OSError:
        return None

    def key(name):
        ds = [int(d) for d in re.findall(r"\d+", name)]
        return ((ds or [0])[0], name)
    return sorted(names, key=key)[0] if names else None


def scorecard(repo, suite_dir, gt_dir=None, timeout=120):
    """GT-scorecard 复跑（D2 件复用）：逐 battle 实跑 scorer 子进程。
    布局=<suite>/battle-N/G-<gen>/（会话）+<gt-dir>/<gen>.json（GT；缺省
    <suite>../gt——battle.py/metrics.py 同源）。无 GT/无会话=skip 记因；
    scorer rc∉{0,1}=error 记因；聚合=微平均（Σ命中/ΣGT+Σfp/Σ活发现）。"""
    suite_dir = os.path.abspath(suite_dir)
    if not os.path.isdir(suite_dir):
        raise GateEnvError("评测套件目录不存在: %s" % suite_dir)
    gtd = gt_dir or os.path.join(os.path.dirname(suite_dir), "gt")
    # 评分器=本件自仓资产（tests/eval_range_recall.py 与 gate 同 checkout 单源），
    # 不随 --repo 走——被审仓可以是任意克隆，判分核不可被被审方替换（eval integrity）。
    scorer = os.path.join(REPO_ROOT, SCORER_REL)
    if not os.path.isfile(scorer):
        raise GateEnvError("GT-scorecard 评分器缺失: %s" % scorer)
    try:
        names = sorted(os.listdir(suite_dir))
    except OSError as e:
        raise GateEnvError("套件目录不可读: %s" % e)
    battles, skipped, errors = [], [], []
    for name in names:
        m = _BATTLE_RE.match(name)
        if not m:
            continue
        home = os.path.join(suite_dir, name)
        n = int(m.group(1))
        gen = _gen_of(home)
        if gen is None:
            skipped.append({"n": n, "reason": "no-session"})
            continue
        gt_path = os.path.join(gtd, gen + ".json")
        if not os.path.isfile(gt_path):
            skipped.append({"n": n, "gen": gen, "reason": "no-gt"})
            continue
        try:
            r = subprocess.run(
                [sys.executable, scorer, "--session", os.path.join(home, gen),
                 "--ground-truth", gt_path, "--baseline", "0"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            errors.append({"n": n, "gen": gen, "reason": "scorer-timeout"})
            continue
        mm = _RECALL_OUT.search(r.stdout or "")
        if r.returncode not in (0, 1) or mm is None:
            errors.append({"n": n, "gen": gen, "reason": "scorer-rc%d" % r.returncode,
                           "detail": (r.stderr or r.stdout or "")[-200:]})
            continue
        hits, total = int(mm.group(2)), int(mm.group(3))
        fp, active = fp_of_session(os.path.join(home, gen))
        battles.append({
            "n": n, "gen": gen,
            "recall": round(hits / total, 4) if total else 0.0,
            "hits": hits, "total": total, "fp": fp, "active": active,
            "fp_rate": round(fp / active, 4) if active else 0.0,
            "scorer_rc": r.returncode})
    battles.sort(key=lambda b: b["n"])
    th, tt = sum(b["hits"] for b in battles), sum(b["total"] for b in battles)
    tf, ta = sum(b["fp"] for b in battles), sum(b["active"] for b in battles)
    return {"battles": battles,
            "aggregate": {"recall": round(th / tt, 4) if tt else 0.0,
                          "hits": th, "total": tt, "fp": tf, "active": ta,
                          "fp_rate": round(tf / ta, 4) if ta else 0.0},
            "skipped": skipped, "errors": errors}


# ==================================================== delta+棘轮判决 ==

def compute_delta(before, after):
    """前后对比 delta（召回/误报主面+计数上下文）；缺方值=None。"""

    def leg(name, key):
        b = before.get(key) if before else None
        a = after.get(key) if after else None
        d = round(a - b, 4) if (b is not None and a is not None) else None
        return {"before": b, "after": a, "delta": d}
    return {"recall": leg("recall", "recall"),
            "fp_rate": leg("fp_rate", "fp_rate"),
            "hits": leg("hits", "hits"), "total": leg("total", "total"),
            "fp": leg("fp", "fp")}


def verdict_of(delta, max_recall_regression, max_fp_regression):
    """棘轮判决：回退>阈值=reject（回退≤阈值=容忍通过——阈值语义钉）。"""
    reasons = []
    r = delta["recall"]
    if None not in (r["before"], r["after"]):
        reg = r["before"] - r["after"]
        if reg > max_recall_regression + EPS:
            reasons.append("召回率回退 %.4f>阈值 %.4f（宪法#43 北极星）"
                           % (reg, max_recall_regression))
    f = delta["fp_rate"]
    if None not in (f["before"], f["after"]):
        reg = f["after"] - f["before"]
        if reg > max_fp_regression + EPS:
            reasons.append("误报率上升 %.4f>阈值 %.4f" % (reg, max_fp_regression))
    return ("reject" if reasons else "pass"), reasons


def load_baseline(path):
    """baseline 读：缺文件=None（collect-first 首跑）；坏 JSON=fail-closed。"""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except ValueError as e:
        raise GateEnvError("baseline 损坏（fail-closed）: %s: %s" % (path, e))
    if not isinstance(doc, dict) or "aggregate" not in doc:
        raise GateEnvError("baseline 形状坏（缺 aggregate）: %s" % path)
    return doc


def write_baseline(path, doc):
    """baseline 原子写（schema_version/arm/battles/aggregate 四键齐）。"""
    out = {"schema_version": 1, "arm": doc.get("arm", "tanyin"),
           "battles": doc.get("battles", []),
           "aggregate": doc.get("aggregate", {})}
    _atomic_write(path, json.dumps(out, ensure_ascii=False, indent=1,
                                   sort_keys=True) + "\n")
    return out


def _ratchet_ok(old_agg, new_agg):
    """棘轮只紧不松：新聚合召回率不低于旧、误报率不高于旧（ε 容差）。"""
    if old_agg.get("recall") is not None and \
            new_agg.get("recall", 0.0) < old_agg["recall"] - EPS:
        return False
    if old_agg.get("fp_rate") is not None and \
            new_agg.get("fp_rate", 0.0) > old_agg["fp_rate"] + EPS:
        return False
    return True


# ============================================================== CLI ==

def _default_home():
    return os.environ.get("TANYIN_HOME") or os.path.join(
        os.path.expanduser("~"), ".tanyin")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="capability_gate",
        description="评测棘轮：能力件变更合并前 GT-scorecard 增量对比（rc 0=过 "
                    "1=拒合并 2=环境）")
    ap.add_argument("--repo", default=REPO_ROOT, help="仓根（缺省=本件所在仓）")
    ap.add_argument("--base", default="HEAD", help="对比基线 ref（缺省 HEAD）")
    ap.add_argument("--suite", default=os.path.join(_default_home(), "battles"),
                    help="评测套件=battle 家目录根（缺省 $TANYIN_HOME/battles）")
    ap.add_argument("--gt-dir", default=None,
                    help="GT 目录（缺省 <suite>../gt——battle.py 同源）")
    ap.add_argument("--baseline",
                    default=os.path.join(_default_home(), "capability-baseline.json"),
                    help="棘轮 baseline 文件（缺省 $TANYIN_HOME/capability-baseline.json）")
    ap.add_argument("--out", default=None, help="delta JSON 落盘路径（可选）")
    ap.add_argument("--max-recall-regression", type=float, default=0.0,
                    help="召回率回退容忍阈（默认 0=棘轮不退）")
    ap.add_argument("--max-fp-regression", type=float, default=0.0,
                    help="误报率上升容忍阈（默认 0=棘轮不退）")
    ap.add_argument("--update-baseline", action="store_true",
                    help="过门后把本次聚合写入 baseline（只紧不松）")
    ap.add_argument("--hook", action="store_true",
                    help="git hook 形态：单行 terse 输出（rc 契约同）")
    a = ap.parse_args(argv)

    def emit(verdict, note=""):
        if a.hook:
            tag = {"pass": "PASS", "reject": "REJECT",
                   "collect-first": "PASS(collect-first)",
                   "env": "ENV-SKIP"}.get(verdict, "ENV-SKIP")
            print("capability-gate: %s %s" % (tag, note))

    doc = {"schema_version": 1, "gate": "capability-ratchet-v1", "arm": "tanyin",
           "base": a.base, "changes": None, "eval": None, "delta": None,
           "thresholds": {"recall_max_regression": a.max_recall_regression,
                          "fp_max_regression": a.max_fp_regression},
           "verdict": None, "reasons": []}

    def finish(rc):
        if a.out:
            try:
                _atomic_write(a.out, json.dumps(doc, ensure_ascii=False,
                                                indent=1, sort_keys=True) + "\n")
            except OSError as e:
                emit("env", "delta 落盘失败")
                sys.stderr.write("delta 落盘失败: %s\n" % e)
                return 2
        if not a.hook:
            print(json.dumps({"verdict": doc["verdict"], "reasons": doc["reasons"],
                              "changes": doc["changes"],
                              "delta": doc["delta"]}, ensure_ascii=False,
                             indent=1, sort_keys=True))
        else:
            emit(doc["verdict"] if doc["verdict"] in ("pass", "reject",
                                                      "collect-first") else "env",
                 "; ".join(doc["reasons"])[:160])
        return rc

    # ---- ① 变更检测（无变更=秒过，不触碰评测套件）
    try:
        changes = detect_changes(a.repo, a.base)
    except GateEnvError as e:
        doc.update({"verdict": "env-error", "reasons": [str(e)]})
        return finish(2)
    doc["changes"] = changes
    if not changes["changed"]:
        doc["eval"] = {"mode": "skipped-no-changes"}
        doc["verdict"] = "pass"
        return finish(0)

    # ---- ② GT-scorecard 复跑（after 臂）
    try:
        after = scorecard(a.repo, a.suite, gt_dir=a.gt_dir)
        baseline_doc = load_baseline(a.baseline)
    except GateEnvError as e:
        doc.update({"verdict": "env-error", "reasons": [str(e)]})
        return finish(2)
    doc["eval"] = {"mode": None, "after": after["aggregate"],
                   "battles": after["battles"], "skipped": after["skipped"],
                   "errors": after["errors"]}
    if not after["battles"]:
        doc["verdict"] = "env-error"
        doc["reasons"] = ["评测套件零可评分战（skip=%d error=%d——环境不可验"
                          "证即拒过，fail-closed）" % (len(after["skipped"]),
                                                       len(after["errors"]))]
        return finish(2)

    # ---- ③ 棘轮判决（before 臂=baseline 文件；缺=collect-first 首跑入册）
    if baseline_doc is None:
        doc["eval"]["mode"] = "collect-first"
        doc["delta"] = compute_delta(None, after["aggregate"])
        doc["verdict"] = "collect-first"
        write_baseline(a.baseline, {"arm": "tanyin", "battles": after["battles"],
                                    "aggregate": after["aggregate"]})
        return finish(0)
    before = baseline_doc["aggregate"]
    doc["eval"]["mode"] = "baseline-vs-rerun"
    doc["eval"]["before"] = before
    doc["delta"] = compute_delta(before, after["aggregate"])
    verdict, reasons = verdict_of(doc["delta"], a.max_recall_regression,
                                  a.max_fp_regression)
    if a.update_baseline and verdict == "pass":
        if _ratchet_ok(before, after["aggregate"]):
            write_baseline(a.baseline, {"arm": "tanyin",
                                        "battles": after["battles"],
                                        "aggregate": after["aggregate"]})
        else:
            verdict = "reject"
            reasons = reasons + ["--update-baseline 拒更：棘轮只紧不松"
                                 "（baseline 未动）"]
    doc["verdict"] = verdict
    doc["reasons"] = reasons
    return finish(1 if verdict == "reject" else 0)


if __name__ == "__main__":
    sys.exit(main())
