# -*- coding: utf-8 -*-
"""知识库机械运算单源（批次 5；铁律 7——语义提炼禁入，本模块只做：
schema 校验/脱敏哨兵/去重哈希/确定性导出/三元组匹配/基线查表/CPE 离线匹配）。

载体（R7）：仓库 knowledge/=种子库（format_version=kn-v1；批次 6 安装器拷贝至
$TANYIN_HOME/knowledge/）；CLI 一律 --knowledge-dir 参数化；种子库只读纪律——
指向仓库 knowledge/ 时一切写子命令（source-register/approve/commit/promote/demote/
client-map add）REJECT（exit 1，防 CI 误写种子）。退出码对齐 Strix：
0=通过 / 1=门禁失败（Reject） / 2=用法或环境问题（KnowledgeError）。"""
import datetime
import hashlib
import json
import os
import re

from . import core
from .core import esc, unesc
from .phases_engine import parse_yaml
from .query_cmds import parse_kv, latest_by, _cell
from . import special
from .graph_cmds import _build, _scope_root_targets, reachable_gap_cells

FORMAT_VERSION = "kn-v1"
DIRS = ("concepts", "precedents", "entities", "targets", "patterns/core",
        "patterns/learned", "business", "retros", "methodology", "cve",
        "sources", "staging/pages", "checklists")
FILES = {"format_version": FORMAT_VERSION + "\n"}

# R7 种子库只读纪律：写子命令守卫集（client-map 按 add 动词判——next/list 只读）
WRITE_SUBS = ("source-register", "approve", "commit", "promote", "demote")


class KnowledgeError(Exception):
    """exit 2：结构/版本/环境问题。"""


class Reject(Exception):
    """exit 1：门禁失败（种子库只读/校验不过/状态机非法迁移）。"""


def repo_seed_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge"))


def load_ctx(kdir):
    """版本门：format_version 不匹配=拒绝操作并提示迁移（契约 14 §1）。"""
    if not os.path.isdir(kdir):
        raise KnowledgeError("knowledge 目录不存在: " + kdir)
    fv = os.path.join(kdir, "format_version")
    if not os.path.isfile(fv) or open(fv, encoding="utf-8").read().strip() != FORMAT_VERSION:
        raise KnowledgeError("format_version 不匹配（期望 %s）——拒绝操作，先跑迁移/重铸" % FORMAT_VERSION)
    return kdir


def guard_writable(kdir, sub, rest):
    """R7：种子库只读——写子命令指向仓库 knowledge/ 时 REJECT（exit 1）。"""
    guarded = sub in WRITE_SUBS or (sub == "client-map" and "add" in rest)
    if not guarded:
        return
    seed = repo_seed_root()
    if os.path.abspath(kdir) == seed:
        raise Reject("种子库只读（仓库 knowledge/ = 发行内容；写操作请在运行时库执行）: " + kdir)


def init(kdir):
    """骨架初始化（幂等：已初始化=PASS no-op）。"""
    os.makedirs(kdir, exist_ok=True)
    for sub in DIRS:
        os.makedirs(os.path.join(kdir, sub), exist_ok=True)
    for name, content in FILES.items():
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
    for name in ("index.md", "log.md", "overview.md"):
        p = os.path.join(kdir, name)
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s\n\n（init 生成；commit 时重生成 index/overview）\n" % name[:-3])
    return 0


# ---------------------------------------------------------------------------
# 批次 5 T10：语源登记 + staging 状态机 + lint 机器检查四件
# ---------------------------------------------------------------------------

TAB = "\t"
TSV_TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
STAGING_COLS = ("staging_id", "page_id", "class", "title", "source_id", "status",
                "checksum", "created", "approved_by", "approved_at")
SOURCES_COLS = ("source_id", "origin", "path", "sha256", "license", "note", "registered_at")
ORIGINS = ("cnpen", "vulnclaw", "bughunter", "threatswarm", "cep", "internal")
# 脱敏哨兵知识侧补充形态（R7/T10 ②）：真域名/IP 零容忍。凭据与占位符形态
# 单源走 special.scan_text（redact 面行为零变，故域名/IP 不进 PLAIN_PATTERNS
# ——账本/报告里 shop.example 系合法 scope 值，进红面即全面误报）。
DOMAIN_RE = re.compile(r"(?i)\b[a-z0-9][a-z0-9-]*\.(example|test|com|net|org|cn|io|co|dev|app|info|biz|xyz|shop|api|local|internal|cloud|online|site|top|vip|edu|gov)\b")
IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
CLIENT_RE = re.compile(r"^CLIENT-\d{2,}$")
WINDOW_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}$")
ID_PREFIX = {"technique": "CP", "precedent": "PR", "entity": "EN", "retro": "RT",
             "pattern": "PT", "business": "BZ"}

# 契约 14 §2 机器表（六类；kind→(目录, 必填集, 枚举 dict)；vocab_version 全页必填=R14）
_STATUS_T = ("core", "learned", "demoted")
_COST = ("1", "2", "3")
PAGE_SCHEMAS = {
    "technique": ("concepts",
                  ("id", "kind", "class", "title", "vocab_version", "vuln_class",
                   "applicability", "cost_hint", "last_verified", "status", "source_id"),
                  {"kind": ("technique",), "class": ("K5",), "status": _STATUS_T,
                   "cost_hint": _COST}),
    "precedent": ("precedents",
                  ("id", "kind", "class", "title", "client", "scope_asset", "window",
                   "triples", "outcome", "cost_hint", "last_verified", "status",
                   "source_id"),
                  {"kind": ("precedent",), "class": ("K2",), "status": _STATUS_T,
                   "cost_hint": _COST}),
    "entity": ("entities",
               ("id", "kind", "entity", "aliases", "occurrences", "pattern_stats",
                "vocab_version", "status", "last_verified"),
               {"kind": ("entity",), "status": _STATUS_T}),
    "retro": ("retros",
              ("id", "kind", "client", "window", "missed", "trigger_gap",
               "weak_channel", "writeback", "vocab_version", "status", "last_verified"),
              {"kind": ("retro",), "status": _STATUS_T}),
    "pattern": ("patterns",
                ("id", "kind", "use", "vuln_class", "sample_brief", "vocab_version",
                 "status", "last_verified"),
                {"kind": ("pattern",), "use": ("ok-sample", "false-positive"),
                 "status": _STATUS_T}),
    "business": ("business",
                 ("id", "kind", "industry", "checklist_brief", "vocab_version",
                  "status", "last_verified"),
                 {"kind": ("business",), "status": _STATUS_T}),
}
# lint 扫描区=staging/pages + 六类正式区（patterns 含 core/learned 两目录；
# targets/cve/methodology 无契约 14 §2 schema，不在 lint 面）
LINT_ZONES = ("staging/pages", "concepts", "precedents", "entities", "retros",
              "business", "patterns/core", "patterns/learned")


def norm_title(t):
    """R10 标题归一窄函数（norm.py 语义同源新窄函数，不碰 norm 轨）：全角→半角/
    去全部空白/小写。"""
    out = []
    for ch in str(t):
        o = ord(ch)
        if o == 0x3000:
            out.append(" ")
        elif 0xFF01 <= o <= 0xFF5E:
            out.append(chr(o - 0xFEE0))
        else:
            out.append(ch)
    return re.sub(r"\s+", "", "".join(out)).lower()


def dedup_key(kind, vuln_class, title):
    return hashlib.sha256((kind + "\x00" + (vuln_class or "") + "\x00" + norm_title(title))
                          .encode("utf-8")).hexdigest()


def repo_shared_vocab():
    return os.path.abspath(os.path.join(repo_seed_root(), "..", "shared", "VOCAB.md"))


def vocab_supported():
    """R14：合法词表版本集合=shared/VOCAB.md 的 version 行。"""
    try:
        with open(repo_shared_vocab(), encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("version:"):
                    return {ln.split(":", 1)[1].strip()}
    except OSError:
        pass
    return set()


def vocab_keys():
    """词表键全集（wstg-* 行；细类=wstg-XX:sub 形按父键判）。"""
    keys = set()
    try:
        with open(repo_shared_vocab(), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln.startswith("- wstg-"):
                    keys.add(ln[2:].strip())
    except OSError:
        pass
    return keys


def split_page(text):
    """页拆分：--- front-matter + 正文；返回 (fm dict 或 None=解析失败, fm 原文, body)。"""
    if text.startswith("---"):
        lines = text.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm_raw = "\n".join(lines[1:i])
                try:
                    return parse_yaml(fm_raw), fm_raw, "\n".join(lines[i + 1:])
                except Exception:
                    return None, fm_raw, "\n".join(lines[i + 1:])
    return {}, "", text


def read_page(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _append_log(kdir, ts, event, page_id, detail):
    p = os.path.join(kdir, "log.md")
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write("%s|%s|%s|%s\n" % (ts, event, page_id, detail))


def _read_tsv(path, cols):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln or ln == TAB.join(cols):
                continue
            rows.append([unesc(c) for c in ln.split(TAB)])
    return rows


def _write_tsv(path, cols, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(TAB.join(cols) + "\n")
        for r in rows:
            f.write(TAB.join(esc(str(c)) for c in r) + "\n")


def next_source_id(kdir):
    """SOURCES.tsv 行键 <KP>-NNNN 下一号（TSV 载体，非目录文件——与 next_id 分立）。"""
    mx = 0
    for r in _read_tsv(os.path.join(kdir, "sources", "SOURCES.tsv"), SOURCES_COLS):
        m = re.match(r"^KP-(\d{4})$", str(r[0]))
        if m:
            mx = max(mx, int(m.group(1)))
    return "KP-%04d" % (mx + 1)


def next_id(kdir, sub_dir, prefix):
    """目录内 <prefix>-NNNN 下一号（四位零填充字典序=时间序；契约 14 §6）。"""
    d = os.path.join(kdir, sub_dir.split("/")[0])
    mx = 0
    if os.path.isdir(d):
        for root, _dirs, files in os.walk(d):
            for fn in files:
                m = re.match("^" + prefix + "-(\d{4})\.md$", fn)
                if m:
                    mx = max(mx, int(m.group(1)))
    return "%s-%04d" % (prefix, mx + 1)


def source_register(kdir, path, origin, license_, note, ts):
    """KP 语源登记（契约 14 §5）：sha256 对原始字节流式计算；SOURCES.tsv 追加。"""
    if origin not in ORIGINS:
        raise Reject("origin 枚举越界: %r（允许 %s）" % (origin, "/".join(ORIGINS)))
    if not ts or not TSV_TS.match(ts):
        raise KnowledgeError("--timestamp 必填（ISO8601；G-23 禁墙钟）")
    if not path or not os.path.isfile(path):
        raise KnowledgeError("语源文件不存在: " + str(path))
    if not license_:
        raise KnowledgeError("--license 必填（外部语料许可凭证）")
    sid = next_source_id(kdir)
    rows = _read_tsv(os.path.join(kdir, "sources", "SOURCES.tsv"), SOURCES_COLS)
    sha = file_sha256(path)
    rows.append([sid, origin, path, sha, license_, note, ts])
    _write_tsv(os.path.join(kdir, "sources", "SOURCES.tsv"), SOURCES_COLS, rows)
    _append_log(kdir, ts, "source-register", sid, "origin=%s sha=%s" % (origin, sha[:12]))
    print(sid)
    return 0


def lint_page(kdir, rel, fm, fm_raw, body, vocab, vkeys, source_ids):
    """单页机器检查：①schema（契约 14 §2）②脱敏哨兵 ④词表版本 ⑤CVE 核验标记
    +引用闭合（client 形态 R12/window/source_id→SOURCES.tsv）。③dedup 在汇总层。"""
    problems = []
    if fm is None:
        return ["front-matter 解析失败（受限 YAML 子集）"]
    kind = fm.get("kind")
    if kind not in PAGE_SCHEMAS:
        return ["kind 不在六类: %r" % (kind,)]
    _dir, required, enums = PAGE_SCHEMAS[kind]
    for f in required:
        if f not in fm or fm[f] in ("", [], None):
            problems.append("缺必填字段 %s" % f)
    for f, allowed in enums.items():
        if f in fm and str(fm[f]) not in allowed:
            problems.append("%s 枚举越界: %r" % (f, fm[f]))
    pid = str(fm.get("id", ""))
    if rel.startswith("staging/pages"):
        if not re.match(r"^STG-\d{4}$", pid):
            problems.append("staging 页 id 须 STG-NNNN: %r" % pid)
    elif not re.match(r"^" + ID_PREFIX[kind] + r"-\d{4}$", pid):
        problems.append("页 id 前缀须 %s-NNNN: %r" % (ID_PREFIX[kind], pid))
    # ② 脱敏哨兵：占位符+凭据形态（special.scan_text 单源）+ 真域名/IP（知识侧补充）
    for name, ln, _col in special.scan_text(fm_raw + "\n" + body):
        problems.append("泄漏形态[%s] 第 %d 行" % (name, ln))
    for ln, line in enumerate((fm_raw + "\n" + body).splitlines(), 1):
        if DOMAIN_RE.search(line):
            problems.append("泄漏形态[真域名形态] 第 %d 行" % ln)
        if IP_RE.search(line):
            problems.append("泄漏形态[IP 形态] 第 %d 行" % ln)
    # ④ 词表版本（R14）+ vuln_class 键闭合
    if fm.get("vocab_version") not in vocab:
        problems.append("vocab_version 不在支持集: %r" % (fm.get("vocab_version"),))
    for vc in str(fm.get("vuln_class", "")).split(";"):
        vc = vc.strip()
        if vc and vc.split(":", 1)[0] not in vkeys:
            problems.append("vuln_class 不在词表: %r" % vc)
    # ⑤ CVE 核验标记（R11）：cve_refs 非空则 cve_verified 逐个覆盖
    refs = [c for c in str(fm.get("cve_refs", "")).split(";") if c.strip()]
    verified = set()
    for v in fm.get("cve_verified", []) or []:
        if isinstance(v, dict) and v.get("cve"):
            verified.add(str(v["cve"]))
    for c in refs:
        if c.strip() not in verified:
            problems.append("cve_refs 未核验: %s（缺 cve_verified 行）" % c.strip())
    # 引用闭合：client 形态（R12）/窗口格式/source_id（契约 14 §2）
    if fm.get("client") and not CLIENT_RE.match(str(fm["client"])):
        problems.append("client 非 CLIENT-NN 形态: %r" % (fm["client"],))
    if fm.get("window") and not WINDOW_RE.match(str(fm["window"])):
        problems.append("window 非 YYYY-MM-DD..YYYY-MM-DD: %r" % (fm["window"],))
    sid = str(fm.get("source_id", ""))
    if sid:
        if not re.match(r"^KP-\d{4}$", sid):
            problems.append("source_id 非 KP-NNNN: %r" % sid)
        elif sid not in source_ids:
            problems.append("source_id 引用不闭合（SOURCES.tsv 缺 %s）" % sid)
    return problems


def _class_counts(results):
    out = {}
    for _rel, _p, _ok, fm in results:
        c = str(fm.get("class", ""))
        if c:
            out[c] = out.get(c, 0) + 1
    return out


def _stage_sync(kdir, ts, results, staged_rows):
    """staging.tsv 十列状态机同步（R8 机器索引）：lint 过的 staged 页→lint-passed；
    状态机唯一载体=staging.tsv（lint 不回写页 front-matter——校验器不改被校验物，
    checksum 才能盯文件漂移；页内 staging_status 仅记入库态，commit 时摘除）。"""
    by_id = {r[1]: r for r in staged_rows}
    for rel, path_md, ok, fm in results:
        if not rel.startswith("staging/pages"):
            continue
        pid = str((fm or {}).get("id", "")) or os.path.basename(path_md)[:-3]
        row = by_id.get(pid)
        checksum = file_sha256(path_md)
        if row is None:
            row = [pid, pid, str((fm or {}).get("class", "")),
                   str((fm or {}).get("title", "")), str((fm or {}).get("source_id", "")),
                   "staged", checksum, ts, "", ""]
            staged_rows.append(row)
            by_id[pid] = row
        row[6] = checksum
        if ok and row[5] == "staged":
            row[5] = "lint-passed"
        elif not ok and row[5] not in ("approved", "rejected"):
            row[5] = "staged"
    _write_tsv(os.path.join(kdir, "staging", "staging.tsv"), STAGING_COLS, staged_rows)
    return staged_rows


def lint(kdir, ts):
    """lint 机器检查（契约 14 §4）：遍历 staging/pages+六类正式区；输出 PASS n=M 或
    FAIL+逐页缺口清单；dedup 查重在汇总层（R10）；staging 过页 staged→lint-passed。"""
    if not ts or not TSV_TS.match(ts):
        raise KnowledgeError("--timestamp 必填（ISO8601；G-23 禁墙钟）")
    vocab, vkeys = vocab_supported(), vocab_keys()
    source_ids = {r[0] for r in _read_tsv(os.path.join(kdir, "sources", "SOURCES.tsv"),
                                          SOURCES_COLS)}
    staged_rows = _read_tsv(os.path.join(kdir, "staging", "staging.tsv"), STAGING_COLS)
    results, dedup_groups, checked, fails = [], {}, 0, 0
    for zone in LINT_ZONES:
        d = os.path.join(kdir, zone)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md"):
                continue
            path_md = os.path.join(d, fn)
            rel = zone + "/" + fn
            fm, fm_raw, body = split_page(read_page(path_md))
            problems = lint_page(kdir, rel, fm, fm_raw, body, vocab, vkeys, source_ids)
            checked += 1
            ok = not problems
            if not ok:
                fails += 1
                print("FAIL %s: %s" % ((fm or {}).get("id", fn), "; ".join(problems)))
            _append_log(kdir, ts, "lint", str((fm or {}).get("id", fn)),
                        "pass" if ok else "fail=%d" % len(problems))
            if fm is not None:
                results.append((rel, path_md, ok, fm))
                k = dedup_key(str(fm.get("kind", "")), str(fm.get("vuln_class", "")),
                              str(fm.get("title", "")))
                dedup_groups.setdefault(k, []).append(str(fm.get("id", fn)))
    # ③ dedup 查重（R10）：同键组 >1 → 全组 FAIL 附键值
    for k, ids in sorted(dedup_groups.items()):
        if len(ids) > 1:
            fails += 1
            print("FAIL dedup 重复组 %s…: %s" % (k[:12], ", ".join(sorted(ids))))
    for c, n in sorted(_class_counts(results).items()):
        if n >= 8:
            print("WARN 人审合并建议: class=%s n=%d（语义近重复合并不实现——R10/G-30 登记）"
                  % (c, n))
    # K1 基线覆盖率断言（裁决 A：CLI 只校验枚举/格式/覆盖率，评定的语义判断不进 CLI）；
    # 无基线文件的库跳过（init 运行时库不带基线；种子库/发行库必过此门）
    brows = baseline_rows(kdir)
    if brows is not None:
        seen = {}
        for r in brows:
            key = r[0]
            seen[key] = seen.get(key, 0) + 1
            if key not in vkeys and ":" not in key:
                fails += 1
                print("FAIL K1 基线外行: %s" % key)
            elif ":" in key and key.split(":", 1)[0] not in vkeys:
                fails += 1
                print("FAIL K1 细类行父键越界: %s" % key)
            try:
                sev_v = float(r[1])
                if not 0 < sev_v <= 1:
                    raise ValueError
            except ValueError:
                fails += 1
                print("FAIL K1 severity_expect 值域: %s=%r" % (key, r[1]))
            if r[2] not in ("1", "2", "3"):
                fails += 1
                print("FAIL K1 cost_hint 枚举越界: %s=%r" % (key, r[2]))
            if r[4] not in vocab:
                fails += 1
                print("FAIL K1 vocab_version 越界: %s=%r" % (key, r[4]))
        for vk in sorted(vkeys):
            if seen.get(vk, 0) != 1:
                fails += 1
                print("FAIL K1 基线覆盖缺口: %s 行数=%d（VOCAB 每 wstg-* 键须恰一行）"
                      % (vk, seen.get(vk, 0)))
    _stage_sync(kdir, ts, results, staged_rows)
    if fails:
        print("FAIL checked=%d failed_groups=%d" % (checked, fails))
        return 1
    print("PASS n=%d" % checked)
    return 0


def h_source_register(ctx, rest):
    kv, _pos = parse_kv(rest)
    return source_register(ctx, kv.get("path", ""), kv.get("origin", ""),
                           kv.get("license", ""), kv.get("note", ""),
                           kv.get("timestamp", ""))


def h_lint(ctx, rest):
    kv, _pos = parse_kv(rest)
    return lint(ctx, kv.get("timestamp", ""))


# ---------------------------------------------------------------------------
# 批次 5 T11：approve/commit/export/match/neighbors
# ---------------------------------------------------------------------------

COMMIT_TARGET = {"technique": "concepts", "precedent": "precedents",
                 "entity": "entities", "retro": "retros", "business": "business",
                 "pattern": "patterns/learned"}


def approve(kdir, page, approver, ts, reject=False, reason=""):
    """staging 页 lint-passed→approved（否则 Reject）；staging.tsv+log.md 双落。"""
    if not ts or not TSV_TS.match(ts):
        raise KnowledgeError("--timestamp 必填（ISO8601；G-23 禁墙钟）")
    if not reject and not approver:
        raise KnowledgeError("--approver 必填（人工审批载体）")
    path = os.path.join(kdir, "staging", "staging.tsv")
    rows = _read_tsv(path, STAGING_COLS)
    row = next((r for r in rows if r[1] == page), None)
    if row is None:
        raise Reject("staging 无此页: %s" % page)
    if reject:
        if row[5] in ("approved", "rejected"):
            raise Reject("状态机非法迁移: %s → rejected（当前 %s）" % (page, row[5]))
        row[5] = "rejected"
        _write_tsv(path, STAGING_COLS, rows)
        _append_log(kdir, ts, "reject", page, "reason=%s" % (reason or "人审不过"))
        print("rejected: " + page)
        return 0
    if row[5] != "lint-passed":
        raise Reject("状态机非法迁移: %s → approved（当前 %s；须先 lint 全过）" % (page, row[5]))
    row[5] = "approved"
    row[8] = approver
    row[9] = ts
    _write_tsv(path, STAGING_COLS, rows)
    _append_log(kdir, ts, "approve", page, "approver=%s" % approver)
    print("approved: " + page)
    return 0


def _commit_transform(text, new_id):
    """页文本变换：id 行改写 + staging_status 摘除（其余字节保留）。"""
    lines = text.split("\n")
    out = [lines[0]]
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        ln = lines[i]
        if re.match(r"^staging_status\s*:", ln):
            i += 1
            continue
        if re.match(r"^id\s*:", ln):
            ln = "id: " + new_id
        out.append(ln)
        i += 1
    if i < len(lines):
        out.extend(lines[i:])
    return "\n".join(out)


def _formal_dedup_keys(kdir, target_dir):
    keys = {}
    d = os.path.join(kdir, target_dir)
    if not os.path.isdir(d):
        return keys
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        fm, _raw, _body = split_page(read_page(os.path.join(d, fn)))
        if isinstance(fm, dict) and fm:
            keys[fn] = dedup_key(str(fm.get("kind", "")), str(fm.get("vuln_class", "")),
                                 str(fm.get("title", "")))
    return keys


def regenerate_index_overview(kdir):
    """index.md/overview.md 重生成（commit 时；页计数确定性文本）。"""
    def count_dir(rel):
        d = os.path.join(kdir, rel)
        return sum(1 for fn in os.listdir(d) if fn.endswith(".md")) if os.path.isdir(d) else 0
    cve_lines = 0
    snap = os.path.join(kdir, "cve", "cve-snapshot.tsv")
    if os.path.isfile(snap):
        with open(snap, encoding="utf-8") as f:
            cve_lines = sum(1 for ln in f if ln.strip())
    total = (count_dir("precedents") + count_dir("entities") + count_dir("concepts")
             + count_dir("retros") + count_dir("business")
             + count_dir("patterns/core") + count_dir("patterns/learned"))
    lines = [
        "# 知识库索引（commit 时重生成；确定性文本）",
        "",
        "- K1 methodology: %d 页（词表锚 shared/VOCAB.md）" % count_dir("methodology"),
        "- K2 precedents: %d 页" % count_dir("precedents"),
        "- K2 entities: %d 页" % count_dir("entities"),
        "- K3 cve: %d 行" % cve_lines,
        "- K5 concepts: %d 页" % count_dir("concepts"),
        "- K6 patterns/core: %d 页" % count_dir("patterns/core"),
        "- K6 patterns/learned: %d 页" % count_dir("patterns/learned"),
        "- K7 business: %d 页" % count_dir("business"),
        "- K8 retros: %d 页" % count_dir("retros"),
        "- K4 指针: shared/DENYLIST.md（库外既有数据文件）",
    ]
    with open(os.path.join(kdir, "index.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    overview = [
        "# 检索入口概览",
        "",
        "- 词表版本: %s（shared/VOCAB.md version 行）" % (",".join(sorted(vocab_supported())) or "未知"),
        "- 正文页总数: %d" % total,
        "- 类目: K1 方法论/K2 先例与实体/K3 CVE 快照/K4 拒绝词表/K5 技法/K6 模式/K7 业务/K8 复盘",
        "",
        "（commit 时重生成；检索入口=LLM 摘要化，本文件只承载机器可重算计数）",
    ]
    with open(os.path.join(kdir, "overview.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(overview) + "\n")


def commit(kdir, page, ts):
    """approved→formal：迁类目录（STG→类前缀重号+staging_status 摘除）+dedup 终检
    （R10）+index/overview 重生成；graph.ndjson 不动（export 独立）。"""
    if not ts or not TSV_TS.match(ts):
        raise KnowledgeError("--timestamp 必填（ISO8601；G-23 禁墙钟）")
    path = os.path.join(kdir, "staging", "staging.tsv")
    rows = _read_tsv(path, STAGING_COLS)
    row = next((r for r in rows if r[1] == page), None)
    if row is None:
        raise Reject("staging 无此页: %s" % page)
    if row[5] != "approved":
        raise Reject("状态机非法迁移: %s → formal（当前 %s；须先 approve）" % (page, row[5]))
    src = os.path.join(kdir, "staging", "pages", page + ".md")
    if not os.path.isfile(src):
        raise Reject("staging 页文件缺失: %s" % src)
    fm, _raw, _body = split_page(read_page(src))
    if not isinstance(fm, dict) or not fm:
        raise Reject("front-matter 解析失败: %s" % page)
    kind = fm.get("kind")
    if kind not in COMMIT_TARGET:
        raise Reject("kind 不在六类: %r" % (kind,))
    target_dir = COMMIT_TARGET[kind]
    new_id = next_id(kdir, target_dir, ID_PREFIX[kind])
    # dedup 终检（R10）：同键已入 formal 页 → REJECT
    key = dedup_key(str(kind), str(fm.get("vuln_class", "")), str(fm.get("title", "")))
    for fn, k in _formal_dedup_keys(kdir, target_dir).items():
        if k == key:
            raise Reject("dedup 重复（R10 终检）: 与 %s 同 kind+vuln_class+标题归一" % fn)
    dst = os.path.join(kdir, target_dir, new_id + ".md")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(_commit_transform(read_page(src), new_id))
    os.remove(src)
    rows = [r for r in rows if r[1] != page]
    _write_tsv(path, STAGING_COLS, rows)
    _append_log(kdir, ts, "commit", new_id, "from=%s" % page)
    regenerate_index_overview(kdir)
    print("committed: %s -> %s" % (page, new_id))
    return 0


def export(kdir):
    """graph.ndjson 全量重建（契约 14 §3）：行序=(source, t 序号) 字典序；实体别名
    合成为 alias 三元组行；created 取 last_verified（确定性——两次执行字节一致）。"""
    lines = []
    for kind_dir in ("precedents", "entities", "concepts", "targets", "business",
                     "retros", "patterns/core", "patterns/learned"):
        d = os.path.join(kdir, kind_dir)
        for fn in sorted(os.listdir(d) if os.path.isdir(d) else []):
            if not fn.endswith(".md"):
                continue
            fm, _raw, _body = split_page(read_page(os.path.join(d, fn)))
            if not isinstance(fm, dict) or not fm or not fm.get("id"):
                continue
            created = str(fm.get("last_verified", ""))
            pid = str(fm["id"])
            klass = str(fm.get("class", ""))
            for i, tr in enumerate(fm.get("triples", []) or []):
                if isinstance(tr, list) and len(tr) == 3:
                    lines.append({"id": "%s:t%d" % (pid, i), "subject": tr[0],
                                  "predicate": tr[1], "object": tr[2],
                                  "source": pid, "class": klass, "created": created})
            aliases = [a.strip() for a in str(fm.get("aliases", "")).split(";") if a.strip()]
            ent = str(fm.get("entity", "")) or pid
            for i, a in enumerate(aliases):
                lines.append({"id": "%s:a%d" % (pid, i), "subject": ent,
                              "predicate": "alias", "object": a,
                              "source": pid, "class": klass, "created": created})
    lines.sort(key=lambda x: (x["source"], x["id"]))
    with open(os.path.join(kdir, "graph.ndjson"), "w", encoding="utf-8", newline="\n") as f:
        for x in lines:
            f.write(json.dumps(x, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n")
    print("exported=%d" % len(lines))
    return 0


def _is_stale(fm, today):
    """R11：cve_verified 任一 verified_at 距 --today 超 365 天=stale。"""
    try:
        t = datetime.date.fromisoformat(today)
    except ValueError:
        return False
    for v in fm.get("cve_verified", []) or []:
        if isinstance(v, dict) and v.get("verified_at"):
            try:
                if (t - datetime.date.fromisoformat(str(v["verified_at"]))).days > 365:
                    return True
            except ValueError:
                continue
    return False


def _match_rows(kdir, client, asset, today):
    """先例三元组命中收集（match/score 共用单源；client=None=不限客户——仅 score 读侧
    因子使用，且只消费命中计数与页 id（CLIENT-NN 脱敏形态由 lint 强制）；
    match 子命令跨客户隔离语义不变）。返回 (hits, expired_lines)：
    hits=[(pid, title, outcome, window, stale 后缀), ...]。"""
    d = os.path.join(kdir, "precedents")
    hits, expired = [], []
    for fn in sorted(os.listdir(d) if os.path.isdir(d) else []):
        if not fn.endswith(".md"):
            continue
        fm, _raw, _body = split_page(read_page(os.path.join(d, fn)))
        if not isinstance(fm, dict) or fm.get("kind") != "precedent":
            continue
        if client is not None and str(fm.get("client", "")) != client:
            continue
        scope_vals = [v.strip() for v in str(fm.get("scope_asset", "")).split(";") if v.strip()]
        if not any(asset in v for v in scope_vals):
            continue
        win = str(fm.get("window", ""))
        if not WINDOW_RE.match(win):
            continue
        pid, title = str(fm.get("id", fn[:-3])), str(fm.get("title", ""))
        stale = " [stale]" if _is_stale(fm, today) else ""
        start, end = win.split("..", 1)
        if start <= today <= end:
            hits.append((pid, title, str(fm.get("outcome", "")), win, stale))
        else:
            expired.append("[expired] %s %s window=%s" % (pid, title, win))
    return hits, expired


def match(kdir, client, asset, today):
    """先例三元组匹配：client 全等 ∧ scope_asset 含 asset 指纹（分号多值任一子串）
    ∧ window 覆盖 today（start≤today≤end；过期不命中并标注 [expired]）；
    [stale]=R11 降权标注。--today 必填（G-34 禁墙钟）。"""
    if not today:
        raise KnowledgeError("--today 必填（G-34：窗口判定基准日显式传入）")
    try:
        datetime.date.fromisoformat(today)
    except ValueError:
        raise KnowledgeError("--today 须 ISO 日期: %r" % today)
    hits, expired = _match_rows(kdir, client, asset, today)
    for pid, title, outcome, win, stale in hits:
        print("%s\t%s\t%s\twindow=%s%s" % (pid, title, outcome, win, stale))
    for ln in expired:
        print(ln)
    print("matched=%d expired=%d" % (len(hits), len(expired)))
    return 0


# ---------------------------------------------------------------------------
# 批次 5 T12：K1 严重度期望基线表（G-24 落表）+ score 只读算分
# ---------------------------------------------------------------------------

BASELINE_COLS = ("vuln_class", "severity_expect", "cost_hint", "rationale_brief",
                 "vocab_version")


def baseline_rows(kdir):
    """K1 基线表行（库无基线文件返回 None——init 运行时库不带基线，
    种子库/发行库必带；批次 6 安装器拷贝同律）。"""
    p = os.path.join(kdir, "methodology", "k1-baseline.tsv")
    if not os.path.isfile(p):
        return None
    return _read_tsv(p, BASELINE_COLS)


def baseline_lookup(kdir, vuln_class):
    """查表次序=细类→wstg 类→缺省 0.5+告警（裁决 A；初值=方法论映射评定人审冻结，
    语义判断不进 CLI——score 只查表）。返回 (severity_expect, 命中行键, warnings)。"""
    rows = baseline_rows(kdir) or []
    by_key = {}
    for r in rows:
        by_key.setdefault(r[0], r)
    vc = str(vuln_class or "").strip()
    if vc in by_key:
        return float(by_key[vc][1]), vc, []
    parent = vc.split(":", 1)[0]
    if parent in by_key:
        return float(by_key[parent][1]), parent, []
    return 0.5, "", ["baseline-miss %s → 缺省 0.5（K1 基线无此行；查表次序细类→类→缺省）"
                     % vc]


def _asset_row_by(s, key):
    """资产行按 id 或 value 精确匹配（--asset 两形态兼容）。"""
    for r in s.rows("assets.tsv"):
        if r[0] == key or _cell(r, "assets.tsv", "value") == key:
            return r
    return None


def score(kdir, goal_dir, vuln_class, asset, today):
    """读侧只读算分（契约 01 勘误冻结公式 priority=severity_expect×asset_value×
    exploitability；Top-K 选择仍=总控决策，契约 09 §4 边界 2 不破——本子命令不改
    任何状态）。三因子可审计复算：
    asset_value=assets.meta bv:<0-1>（未标/未命中=0.5 中性，P3「未标=不加分」对齐）；
    exploitability=0.4×可达（reachable_gap_cells 单源，scope-root 起点集含该资产
    ——R-T7-1 converge 语义）+0.3×(active creds>0)+0.3×(先例命中>0)。
    --today 必填（先例窗口判定；G-34 禁墙钟）。stdout 单行 JSON，双跑字节一致。"""
    if not today:
        raise KnowledgeError("--today 必填（先例命中因子窗口判定；G-34 禁墙钟）")
    try:
        datetime.date.fromisoformat(today)
    except ValueError:
        raise KnowledgeError("--today 须 ISO 日期: %r" % today)
    if not goal_dir or not os.path.isdir(goal_dir):
        raise KnowledgeError("--goal-dir 交战区目录不存在: " + str(goal_dir))
    sev, row_key, warnings = baseline_lookup(kdir, vuln_class)
    s = core.Session(goal_dir)
    nodes, _adj = _build(s)
    reach, _rg, _ug = reachable_gap_cells(s, _scope_root_targets(s, nodes))
    reach_vals = {_cell(r, "assets.tsv", "value") for r in s.rows("assets.tsv")
                  if r[0] in reach}
    reachable = bool(asset) and (asset in reach or asset in reach_vals)
    bv, bv_src = 0.5, "default(未标=0.5 中性)"
    row = _asset_row_by(s, asset) if asset else None
    if row is not None:
        m = re.search(r"\bbv:([01](?:\.\d+)?)", _cell(row, "assets.tsv", "meta"))
        if m:
            bv = min(1.0, float(m.group(1)))
            bv_src = "%s meta bv=%s" % (row[0], m.group(1))
    active = sum(1 for r in latest_by(s.rows("creds.tsv"), "creds.tsv", ["id"]).values()
                 if _cell(r, "creds.tsv", "status") == "active")
    hits, _expired = _match_rows(kdir, None, asset or "", today) if asset else ([], [])
    exploitability = round(0.4 * (1.0 if reachable else 0.0)
                           + 0.3 * (1.0 if active > 0 else 0.0)
                           + 0.3 * (1.0 if hits else 0.0), 4)
    priority = round(sev * bv * exploitability, 4)
    print(json.dumps({
        "severity_expect": sev,
        "asset_value": bv,
        "exploitability": exploitability,
        "priority": priority,
        "sources": {
            "severity_row": row_key,
            "asset_value_source": bv_src,
            "reach_count": len(reach),
            "active_creds": active,
            "match_hits": sorted(h[0] for h in hits),
            "warnings": warnings,
        },
    }, ensure_ascii=False, sort_keys=True))
    return 0


def neighbors(kdir, entity):
    """graph.ndjson 中 subject/object 含实体名的行清单（A8 外推消费入口）。"""
    p = os.path.join(kdir, "graph.ndjson")
    if not os.path.isfile(p):
        raise KnowledgeError("graph.ndjson 不存在——先跑 export")
    n = 0
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            row = json.loads(ln)
            if entity in row["subject"] or entity in row["object"]:
                print("%s\t%s %s %s\tsource=%s"
                      % (row["id"], row["subject"], row["predicate"],
                         row["object"], row["source"]))
                n += 1
    print("neighbors=%d" % n)
    return 0


def h_approve(ctx, rest):
    kv, _pos = parse_kv(rest)
    return approve(ctx, kv.get("page", ""), kv.get("approver", ""),
                   kv.get("timestamp", ""), reject=bool(kv.get("reject")),
                   reason=kv.get("reason", ""))


def h_commit(ctx, rest):
    kv, _pos = parse_kv(rest)
    return commit(ctx, kv.get("page", ""), kv.get("timestamp", ""))


def h_export(ctx, rest):
    return export(ctx)


def h_match(ctx, rest):
    kv, _pos = parse_kv(rest)
    return match(ctx, kv.get("client", ""), kv.get("asset", ""), kv.get("today", ""))


def h_score(ctx, rest):
    kv, _pos = parse_kv(rest)
    return score(ctx, kv.get("goal-dir", ""), kv.get("vuln-class", ""),
                 kv.get("asset", ""), kv.get("today", ""))


def h_neighbors(ctx, rest):
    kv, _pos = parse_kv(rest)
    return neighbors(ctx, kv.get("entity", ""))
