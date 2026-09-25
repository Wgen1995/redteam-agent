# -*- coding: utf-8 -*-
"""tanyin ledger 特殊命令（批次 1 T9）：redact-scan——占位符纪律＋明文凭据模式扫描。

双入口同一逻辑：cli/tanyin-ledger redact-scan ／ cli/tanyin-redact。
契约依据：02a §30（占位符零泄漏=交付前终检，残留=阻断导出非 REJECT 落账）；
占位符白名单【依契约 01】：creds.secret_ref（§3.13＝{{vault:cred-N}} 占位符）与
E-index.repro_command（§3.9「凭据一律 {{vault:cred-N}} 占位符」）——任务简报口径为
「仅 secret_ref 列」，与契约 01 §3.9 冲突，按契约执行（探知项见完工报告）。
账本模式定位=表:行:列；报告文本模式（--target 指向无 13 表的目录/文件）任何
{{vault:}} 残留即泄漏。退出码 0=PASS 1=FAIL(leaks>0) 2=用法/环境。
"""
import os, re, sys

from . import core
from .schemas import TABLES
from .query_cmds import parse_kv, UsageError, usage_guard

TAB = chr(9)
PLACEHOLDER = re.compile(r"\{\{vault:[^}]*\}\}")
SECRET_REF_OK = re.compile(r"^\{\{vault:cred-\d+\}\}$")
# 明文凭据模式【推导】（任务简报列举 password=xxx/AKIA…/私钥头 + 同类 token 形态）
PLAIN_PATTERNS = [
    ("明文私钥头", re.compile(r"BEGIN [A-Z0-9 ]*PRIVATE KEY")),
    ("AWS AccessKey 形态", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("密码赋值形态", re.compile(r"(?i)\b(passwd|password)\s*[=:]\s*[^\s;]+")),
    ("GitHub token 形态", re.compile(r"\bgh[posr]_[A-Za-z0-9]{20,}\b")),
    ("API key 形态", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("GitLab token 形态", re.compile(r"\bglpat-[A-Za-z0-9_-]{15,}\b")),
    ("Netlify token 形态", re.compile(r"\bnp_[A-Za-z0-9]{16,}\b")),
    ("API key 赋值", re.compile(r"(?i)\b(api[_-]?key|apikey)\s*[=:]\s*\S{8,}")),
    ("client_secret 赋值", re.compile(r"(?i)\bclient[_-]?secret\s*[=:]\s*\S{6,}")),
    ("secret 赋值", re.compile(r"(?i)\bsecret\s*[=:]\s*[^\s;]{6,}")),
    ("token 赋值", re.compile(r"(?i)\b(access[_-]?token|auth[_-]?token|token)\s*[=:]\s*[A-Za-z0-9._+/=-]{12,}")),
    ("AWS secret 配置", re.compile(r"(?i)secret_access_key\]?\s*[=:]\s*\S{8,}")),
    ("Authorization Basic", re.compile(r"(?i)authorization\s*[:=]\s*basic\s+[A-Za-z0-9+/=]{8,}")),
    ("Authorization Bearer", re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._-]{10,}")),
    ("会话 cookie", re.compile(r"(?i)\b(phpsessid|jsessionid|sessionid|session|sid)\s*[=:]\s*[A-Za-z0-9,-]{16,}")),
    ("Set-Cookie 反射", re.compile(r"(?i)\bset-cookie\s*:[^\s]{4,}")),
    ("docker 凭据载体", re.compile(r"(?i)_dockercfg|dockerconfigjson")),
    ("数据库连接串", re.compile(r"\b(mysql|mariadb|mongodb|postgresql|postgres|redis|amqp)://[^\s/:@]*:[^\s/@]+@")),
    ("NTLM hash 形态", re.compile(r"\b[0-9a-fA-F]{32}:[0-9a-fA-F]{32}(?::[0-9a-fA-F]{32})?\b")),
    ("Slack token 形态", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("JWT 形态", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.")),
]
PLACEHOLDER_OK_COLS = {("creds.tsv", "secret_ref"), ("E-index.tsv", "repro_command")}
REPORT_SUFFIXES = (".md", ".txt", ".json", ".html", ".csv", ".log", "")


def _iter_table_lines(path):
    """逐行返回 (行号, [未转义字段])；列数畸形不阻断扫描（行级校验归 validate）。"""
    out = []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            out.append((ln, [core.unesc(c) for c in line.split(TAB)]))
    return out


def scan_table(path, tname):
    fields = TABLES[tname]
    leaks = []
    for ln, cells in _iter_table_lines(path):
        for ci, val in enumerate(cells):
            col = fields[ci] if ci < len(fields) else "col%d" % ci
            loc = "%s:%d:%s" % (tname, ln, col)
            if PLACEHOLDER.search(val) and (tname, col) not in PLACEHOLDER_OK_COLS:
                leaks.append((loc, "占位符出现在非白名单列（仅 creds.secret_ref/E-index.repro_command）"))
            if tname == "creds.tsv" and col == "secret_ref" and val.strip() \
                    and not SECRET_REF_OK.match(val.strip()):
                leaks.append((loc, "secret_ref 真值形态（真值永不进账本，§4.10）"))
            for name, pat in PLAIN_PATTERNS:
                if pat.search(val):
                    leaks.append((loc, "明文凭据模式:" + name))
    return leaks


def scan_text(text):
    """纯文本泄漏形态扫描（批次 5 T10 单源化 API；T13/T15 消费同款）——逐行扫
    占位符残留与 PLAIN_PATTERNS 明文凭据形态，返回 [(形态名, 行号, 列号)]；
    占位符行列号为 None（沿用 scan_text_file 原位置格式 %s:%d 不带列）。
    scan_text_file 改调本函数，行为零变（金样 read-redact-scan 钉死）。"""
    hits = []
    for ln, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER.search(line):
            hits.append(("占位符残留", ln, None))
        for name, pat in PLAIN_PATTERNS:
            m = pat.search(line)
            if m:
                hits.append((name, ln, max(1, m.start() + 1)))
    return hits


def scan_text_file(path, rel):
    leaks = []
    try:
        data = open(path, "rb").read(4096)
        if b"\x00" in data:
            return leaks  # 二进制跳过
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return leaks
    for name, ln, col in scan_text(text):
        if col is None:
            leaks.append(("%s:%d" % (rel, ln), "报告残留占位符（P5 占位符零泄漏）"))
        else:
            leaks.append(("%s:%d:%d" % (rel, ln, col), "明文凭据模式:" + name))
    return leaks


def scan_target(target):
    """账本模式（目标含 13 表）／报告文本模式（其余目录/文件）。"""
    leaks = []
    if os.path.isfile(target):
        return scan_text_file(target, os.path.basename(target))
    table_hits = 0
    for tname in TABLES:
        p = os.path.join(target, tname)
        if os.path.isfile(p):
            table_hits += 1
            leaks.extend(scan_table(p, tname))
    if table_hits:
        return leaks
    for root, _dirs, files in os.walk(target):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, target)
            if fn.endswith(".tsv") or os.path.splitext(fn)[1] not in REPORT_SUFFIXES:
                continue
            leaks.extend(scan_text_file(p, rel))
    return leaks


def redact_scan(goal_dir, target=None):
    target = target or goal_dir
    if not os.path.exists(target):
        print("FAIL 环境问题: 目标不存在 " + target)
        return 2
    leaks = scan_target(target)
    if not leaks:
        print("PASS" + TAB + "leaks=0")
        return 0
    print("FAIL" + TAB + "leaks=%d" % len(leaks))
    for loc, why in leaks:
        print(loc + TAB + why)
    return 1


def h_redact_scan(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or set(args) - {"target"}:
        raise UsageError("redact-scan [--target=<路径>]")
    return redact_scan(goal_dir, args.get("target") or None)


def h_reverse_verify(goal_dir, rest):
    """批次 5 T15（R13）：反向验证——P6 沉淀门前把草稿对 session 敏感词集反查。

    敏感词三源：assets.value 全集（域名/IP/URL 型资产）+ creds.username_ref +
    PLAIN_PATTERNS 泄漏形态（单源复用）。形态级只扫明文形态不扫 {{vault:}} 占位符
    ——占位符是脱敏正当形态（契约 01 creds.secret_ref 白名单同源语义；P6 断言
    expect=零命中而 P5 redact-scan 面已另行执法占位符零残留，双检语义不同层）。
    退出码：0=零命中 1=命中清单 2=草稿不存在/用法。"""
    args, pos = parse_kv(rest)
    if pos or set(args) - {"reverse-verify", "target"}:
        raise UsageError("reverse-verify [--target=<draft 路径>]（缺省 report/report-draft.md）")
    target = args.get("target") or os.path.join("report", "report-draft.md")
    p = target if os.path.isabs(target) else os.path.join(goal_dir, target)
    if not os.path.isfile(p):
        sys.stderr.write("环境问题: 草稿不存在 %s（P5 先产 report-draft）\n" % target)
        return 2
    s = core.Session(goal_dir)
    words = set()
    for tname, col in (("assets.tsv", "value"), ("creds.tsv", "username_ref")):
        if not os.path.isfile(os.path.join(goal_dir, tname)):
            continue
        ci = TABLES[tname].index(col)
        for r in s.rows(tname):
            v = r[ci].strip() if ci < len(r) else ""
            if v:
                words.add(v)
    hits = []
    with open(p, encoding="utf-8") as f:
        for i, ln in enumerate(f, 1):
            ln = ln.rstrip("\r\n")
            for w in sorted(words):
                if w in ln:
                    hits.append("%s:%d:资产/账号值 %s" % (target, i, w))
            for name, pat in PLAIN_PATTERNS:
                if pat.search(ln):
                    hits.append("%s:%d:泄漏形态[%s]" % (target, i, name))
    if hits:
        print("FAIL 反向验证命中 %d 处：" % len(hits))
        for h in hits[:50]:
            print("  " + h)
        return 1
    print("零命中（域名/IP/凭据/token 敏感词 %d 项全未出现）" % len(words))
    return 0


HANDLERS = {"redact-scan": usage_guard(h_redact_scan)}
# 批次 5 T15（R-T15-2）：reverse-verify 不经 HANDLERS 注册——registry.all_commands()
# 以 HANDLERS 键集为 44 命令面基名单源（「账本命令零新增」冻结），reverse-verify 是
# tanyin-redact 旗标（phases.yaml 断言文本 `tanyin-redact --reverse-verify`，R13），
# 仅 tanyin-redact 入口与 phases_engine 断言回路两处分发，非 tanyin-ledger 子命令。
REVERSE_VERIFY = usage_guard(h_reverse_verify)
