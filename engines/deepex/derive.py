#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deepex 派生层（W3-P1-1②，契约 07/08）——读取类发现→凭据检查意图（不外发）。

docs/reviews/2026-10-17-exceed-review/03-渗透工作流专家.md P1-1「文件读取利用闭环:
读到配置/密钥→add-cred(kind=session)→cred-obtained 事件→身份差分自动触发（设计已
全备，只差工具卡与技法页）」的引擎面第一段：

    读取类发现（备份/配置/密钥文件） ──派生──> 凭据检查意图卡（kind=deep-dive）

派生纪律三件（全部结构化，不靠措辞自觉）：
① 不外发：意图卡 constraints.egress=forbidden；检查计划只含本地校验（格式/规则/
   重复使用），网络验证面不在本层——须经授权另立意图走 guard 通道。
② 密值不带出：源发现 reproducible_steps 常含原文凭据（password=…），意图卡只携带
   文件路径锚+脱敏摘录——密值落 vault 是总控 add-cred 的事，派生层不复制密值。
③ 引擎不写账本（单写者）：产物=artifacts/derived-cred-intents.json（契约 07 §1
   submissions/<intent-id>/artifacts/ 布局同源），总控验收后落 intents。

RCE 取证模板（③）同层另一文件面：forensics 包（whoami/id/hostname 非破坏三连），
见 forensic_packages()——三连固定禁增删，逐条过 guard deny 机械（黑名单兼容）。"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # engines/deepex → 仓根
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import enforce  # noqa: E402  （guard deny 机械单源——黑名单兼容复用）

USAGE = "用法: derive.py --findings-file=F --out-dir=D [--submission-file=S]\n"

# 读取类发现的敏感文件签名（title+location 联合匹配；文件锚取路径形 token）。
# 边界用 ASCII 类前瞻而非 \b：中文全角括号「（」属 Unicode \w，"​.env（"在 \b 下
# 不成边界会漏配（CJK 邻接坑——测试钉死）。
_X = r"(?![0-9A-Za-z])"
READ_FILE_PATTERNS = (
    ("backup", re.compile(r"(?:backup|\.bak" + _X + r"|\.old" + _X + r"|dump\.sql"
                          + _X + r"|\.sql" + _X + r"|\.sqlite" + _X + r"|\.db"
                          + _X + r")", re.I)),
    ("config", re.compile(r"(?:\.env" + _X + r"|wp-config|config\.\w+|settings\.\w+|"
                          r"database\.ya?ml|application[\w.-]*\.properties|redis\.conf|"
                          r"\.git/config|\.aws/credentials|\.kube/config|web\.config|"
                          r"\.ini" + _X + r"|\.toml" + _X + r")", re.I)),
    ("key", re.compile(r"(?:id_rsa|id_ed25519|\.pem" + _X + r"|\.key" + _X + r"|\.p12"
                       + _X + r"|secrets?[\w.-]*|credentials?[\w.-]*)", re.I)),
)
# 路径形 token 抽取（/backup/db.sql、.env、wp-config.php）
PATH_TOKEN = re.compile(r"(?:/[\w.@-]+)+|\b[\w.-]+\.[A-Za-z]{1,8}\b")
# 密值脱敏：password=/token=/secret=… 与 sk-/Bearer 形（摘录与卡片全域不带密值）
SECRET_ASSIGN = re.compile(
    r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|private[_-]?key)"
    r"(\s*[=:]\s*)(\S.{0,64})", )
SECRET_LITERAL = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b|\bBearer\s+[A-Za-z0-9._-]{8,}\b")
REDACTED = "[已脱敏:本地校验]"

# 凭据检查计划（本地三查——不外发的操作面）
LOCAL_CHECKS = (
    "格式与编码校验（本地）",
    "规则匹配: 密码/密钥/连接串模式（本地）",
    "重复使用与默认口令比对（本地词典）",
)


def redact(text):
    """密值遮蔽：赋值形截断+字面形整段替换——派生层输出全域不带密值。"""
    if not text:
        return text

    def _sub(m):
        return m.group(1) + m.group(2) + REDACTED
    out = SECRET_ASSIGN.sub(_sub, text)
    return SECRET_LITERAL.sub(REDACTED, out)


def strip_payload(text):
    """破坏载荷剥离：deny-list 单源——标题回显含 rm -rf / 等命中模式整段置换。"""
    out = text or ""
    for pat in enforce.DENY_LIST:
        if pat in out:
            out = out.replace(pat, "[载荷已剥离]")
    return out


def read_file_match(finding):
    """读取类发现判定：title+location 命中敏感文件签名→(文件锚, 类别)；否则 None。"""
    text = " ".join(str(finding.get(k, "")) for k in ("title", "location"))
    for kind, pat in READ_FILE_PATTERNS:
        if pat.search(text):
            m = PATH_TOKEN.search(text)
            return (m.group(0) if m else text.strip()[:40]), kind
    return None


def derive_cred_intents(findings):
    """读取类发现→凭据检查意图卡。返回 (intents, skipped)。

    skipped=畸形行计数（非 dict/缺 dedup 键——宽容跳过不崩，计数上报）；
    同 dedup_key_proposed 只派生一次（重复发现=同一条检查意图）。"""
    if not findings:
        return [], 0
    intents, seen, skipped = [], set(), 0
    for f in findings:
        if not isinstance(f, dict) or not f.get("dedup_key_proposed"):
            skipped += 1
            continue
        hit = read_file_match(f)
        if not hit:
            continue
        anchor, kind = hit
        src = f["dedup_key_proposed"]
        if src in seen:
            continue
        seen.add(src)
        excerpt_src = " ".join(str(f.get(k, "")) for k in ("title", "location"))
        intents.append({
            "title": "凭据检查·%s（%s 类）" % (anchor, kind),
            "kind": "deep-dive",
            "origin": "precedent",
            "engine": "deepex-cred",
            "dedup_key_proposed": src + "+cred-check",
            "budget_share": "0;0;0",
            "checks": list(LOCAL_CHECKS),
            "constraints": {
                "egress": "forbidden",
                "note": "凭据材料不外发——仅本地校验；网络验证面须经授权另立意图走 guard 通道",
            },
            "source_finding": src,
            "source_excerpt": redact(excerpt_src)[:120],
            "file_hint": anchor,
        })
    intents.sort(key=lambda i: i["dedup_key_proposed"])
    return intents, skipped


def load_findings(args):
    """--findings-file（裸数组）或 --submission-file（submission.json 取 findings[]）。"""
    if args.get("--findings-file"):
        with open(args["--findings-file"], encoding="utf-8") as fh:
            return json.load(fh), args["--findings-file"]
    with open(args["--submission-file"], encoding="utf-8") as fh:
        return json.load(fh).get("findings", []), args["--submission-file"]
    return None, ""


# ------------------------------------------------------- ③ RCE 取证模板

# 非破坏三连：固定序、无参数、零写入——身份取证最小集（禁增删，测试钉死）。
FORENSIC_TRIO = ("whoami", "id", "hostname")
# 命令执行类发现签名（title+location；中英双形）
RCE_MARKERS = re.compile(
    r"(?:\brce\b|remote\s+code\s+execution|os\s+command\s+injection|"
    r"command\s+injection|code\s+exec(?:ution)?|命令执行|远程代码执行|系统命令注入)", re.I)
# 三连各自的预期匹配（证据卡 expected——输出形状锚，非回显命令名）
FORENSIC_MATCHERS = {
    "whoami": {"matchers": [{"type": "regex", "regex": [r"\S+"]}]},
    "id": {"matchers": [{"type": "word", "words": ["uid="]}]},
    "hostname": {"matchers": [{"type": "regex", "regex": [r"[A-Za-z0-9._-]+"]}]},
}


def is_rce_finding(finding):
    text = " ".join(str(finding.get(k, "")) for k in ("title", "location"))
    return bool(RCE_MARKERS.search(text))


def forensic_packages(findings, extra=None):
    """命令执行类发现→取证包（非破坏三连+证据卡落账锚）。禁删改：

    - extra 非空即拒（ValueError）——模板不可追加/替换/裁剪，含「看起来无害」的
      追加（whoami 也拒：三连就是三连，开了口子就是删改通道）。
    - 三连逐条经 guard deny 机械（deny_forms+deny_hit，cli/ledger 单源）终检——
      黑名单兼容是运行前提不是愿望；发现文本含破坏载荷也不进包体。"""
    if extra:
        raise ValueError("禁删改: 取证模板三连不可增删（extra=%d 项被拒——"
                         "口子一开即是删改通道）" % len(extra))
    if not findings:
        return []
    for c in FORENSIC_TRIO:   # 黑名单兼容终检（单源机械，非措辞自觉）
        for form in enforce.deny_forms([c]):
            hit = enforce.deny_hit(form)
            if hit:
                raise RuntimeError("取证三连 deny 命中（黑名单不兼容）: %s ← %s" % (c, hit))
    packages = []
    for f in findings:
        if not isinstance(f, dict) or not f.get("dedup_key_proposed") or not is_rce_finding(f):
            continue
        packages.append({
            "source_finding": f["dedup_key_proposed"],
            "finding_title": strip_payload(redact(str(f.get("title", ""))))[:80],
            "commands": list(FORENSIC_TRIO),
            "immutable": True,
            "execution_channel": "tanyin-guard exec（request-ticket 落账）",
            "evidence_cards": [
                {"command": c, "capture": "stdout", "redaction": "vault-tokenize",
                 "expected_matcher": FORENSIC_MATCHERS[c]}
                for c in FORENSIC_TRIO
            ],
        })
    packages.sort(key=lambda p: p["source_finding"])
    return packages


def parse_argv(argv):
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


def main(argv):
    args = parse_argv(argv)
    if not (args.get("--findings-file") or args.get("--submission-file")) \
            or not args.get("--out-dir"):
        sys.stderr.write(USAGE)
        return 2
    findings, src = load_findings(args)
    intents, skipped = derive_cred_intents(findings)
    packages = forensic_packages(findings)
    art_dir = os.path.join(args["--out-dir"], "artifacts")
    os.makedirs(art_dir, exist_ok=True)
    doc = {"intents": intents, "source": os.path.basename(src or ""),
           "count": len(intents), "skipped": skipped}
    path = os.path.join(art_dir, "derived-cred-intents.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    fdoc = {"packages": packages, "source": os.path.basename(src or ""),
            "count": len(packages)}
    fpath = os.path.join(art_dir, "forensic-packages.json")
    with open(fpath, "w", encoding="utf-8", newline="\n") as f:
        json.dump(fdoc, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(os.path.join(args["--out-dir"], "operations.log"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("cred-intents: %d 项（源=%s skipped=%d）\n"
                "forensic-packages: %d 包（三连=%s）\n"
                % (len(intents), src, skipped, len(packages), ",".join(FORENSIC_TRIO)))
    print("OK artifacts/derived-cred-intents.json intents=%d skipped=%d"
          % (len(intents), skipped))
    print("OK artifacts/forensic-packages.json packages=%d" % len(packages))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
