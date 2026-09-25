# -*- coding: utf-8 -*-
"""知识库机械运算单源（批次 5；铁律 7——语义提炼禁入，本模块只做：
schema 校验/脱敏哨兵/去重哈希/确定性导出/三元组匹配/基线查表/CPE 离线匹配）。

载体（R7）：仓库 knowledge/=种子库（format_version=kn-v1；批次 6 安装器拷贝至
$TANYIN_HOME/knowledge/）；CLI 一律 --knowledge-dir 参数化；种子库只读纪律——
指向仓库 knowledge/ 时一切写子命令（source-register/approve/commit/promote/demote/
client-map add）REJECT（exit 1，防 CI 误写种子）。退出码对齐 Strix：
0=通过 / 1=门禁失败（Reject） / 2=用法或环境问题（KnowledgeError）。"""
import hashlib
import json
import os
import re

from .core import esc, unesc
from .phases_engine import parse_yaml
from .query_cmds import parse_kv
from . import special

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
