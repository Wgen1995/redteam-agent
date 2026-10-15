# -*- coding: utf-8 -*-
"""Ship Z（v0.9d）：ZhuLong findings 互通导出——zhulong-export 命令。

契约实勘（2026-10-15，只读 ZhuLong 源码
ai-assisted-security-verification-platform）：
  · POST /api/imports（apps/server/src/routes/tasks.ts 端点19）请求体
    ImportCreateBodySchema＝{engineId, sourceDir, projectId, objectId?, envId?}；
  · 鉴权=会话 Cookie zl_sess：POST /api/auth/login {username,password}→Set-Cookie
    （apps/server/src/middleware/auth.ts）；
  · sourceDir=ZhuLong 服务进程可读目录，内容=tanyin@1 mapper 消费的平铺五族
    （apps/server/src/services/mapper-tanyin.ts）：findings.tsv(19 列·权威)/
    E-index.tsv(16 列)/timeline.tsv(8 列·gate-exit+replay 事件)/edges.tsv(7 列·
    attack 边)/EV-*.md+FD-*.md（basename 键·单段名律）＋battle-report.md
    （tanyin manifest required pattern——apps/server/fixtures/tanyin-gold 金样本同构）。

行为：--dry-run 默认——零网络，落导入包目录＋JSON 导入包（字段对齐契约）；
显式 --push 才真发（登录→zl_sess→POST /api/imports）。导出内容一律过 vault
脱敏（tokenize_output 同值——tanyin-guard 单源，漂移钉=tests/test_v09d_zhulong.py）。
Python 3.9 纯 stdlib；只读账本（不持 goal 写锁·写面仅包目录）。
"""
import hashlib
import json
import os
import sys
import urllib.request as _urlreq

from . import vault
from .schemas import TABLES
from .query_cmds import UsageError, usage_guard, parse_kv

TAB = chr(9)
LF = chr(10)
DEFAULT_URL = "http://localhost:3081"   # ZhuLong 服务（同机自持部署面）
PKG_DIR_NAME = "zhulong-export"
PKG_JSON = "zhulong-import.json"
ENGINE_ID = "tanyin"                     # ZhuLong 内置引擎 manifest id（BO14 T1）
_FAMILY = ("findings.tsv", "E-index.tsv", "timeline.tsv", "edges.tsv")


def _tokenize(text, secrets):
    """vault 真值→{{vault:cred-N}} 占位（长值优先）——语义单源=tanyin-guard
    tokenize_output（vault.secrets 已按真值长度降序）；本函数为其库内同值面，
    同值漂移由 tests/test_v09d_zhulong.py TestTokenizeDrift 逐字钉。"""
    for n, s in secrets:
        if s:
            text = text.replace(s, "{{vault:cred-%s}}" % n)
    return text


def _read_rows(gd, name):
    """表→行清单（无头 TSV·滤空行）——read_tsv 同语义的轻读面。"""
    p = os.path.join(gd, name)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return [l for l in f.read().split(LF) if l.strip()]


def _cell(row, table, col):
    i = TABLES[table].index(col)
    return row[i] if i < len(row) else ""


def _int_arg(args, key):
    v = args.get(key)
    if v is None or v is True:
        raise UsageError("zhulong-export 需 --%s=<正整数>" % key.replace("-", "-"))
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise UsageError("--%s 须为整数: %r" % (key, v))
    if n <= 0:
        raise UsageError("--%s 须为正整数: %d" % (key, n))
    return n


def _stale_clean(out_dir):
    """包目录陈旧产物清理（同名重导=确定性再生·防前次 EV/FD 卡残留污染 mapper）。"""
    if not os.path.isdir(out_dir):
        return
    for n in os.listdir(out_dir):
        if (n in _FAMILY or n == "battle-report.md" or n == PKG_JSON
                or n.startswith("EV-") or n.startswith("FD-")):
            p = os.path.join(out_dir, n)
            if os.path.isfile(p):
                os.remove(p)


def _battle_report(gd, fd_cells, ev_rows, ts):
    """battle-report.md（manifest required pattern 命中）——goal+计数+发现清单，
    内容确定性（账本序），导出前整体过脱敏。fd_cells=已切分列清单。"""
    goal = (_read_rows(gd, "goals.tsv") or [""])[0].split(TAB)
    gid = goal[0] if goal else ""
    target = goal[1] if len(goal) > 1 else ""
    objective = goal[2] if len(goal) > 2 else ""
    active = sum(1 for r in fd_cells if _cell(r, "findings.tsv", "status") == "active")
    sup = sum(1 for r in fd_cells if _cell(r, "findings.tsv", "status") == "superseded")
    lines = ["# 探隐战报 · ZhuLong 导出包",
             "goal: " + gid + TAB + "target: " + target,
             "objective: " + objective,
             "generated: " + ts,
             "findings: total=%d active=%d superseded=%d" % (len(fd_cells), active, sup),
             "evidence: %d" % (len(ev_rows) if ev_rows else 0),
             "## 发现清单（账本序）"]
    for r in fd_cells:
        lines.append("- " + TAB.join([
            _cell(r, "findings.tsv", "id"), _cell(r, "findings.tsv", "confidence"),
            _cell(r, "findings.tsv", "impact"),
            _cell(r, "findings.tsv", "exploitation_status"),
            _cell(r, "findings.tsv", "status"), _cell(r, "findings.tsv", "title")]))
    return LF.join(lines) + LF


def build_package(gd, out_dir, ts, secrets):
    """落盘平铺五族+battle-report（全量脱敏）→ (files 清单, counts, warnings)。"""
    os.makedirs(out_dir, exist_ok=True)
    _stale_clean(out_dir)
    files, warnings = [], []
    token_counts = {}

    def emit(name, text):
        if secrets:
            for n, s in secrets:
                if s and s in text:
                    key = "cred-" + n
                    token_counts[key] = token_counts.get(key, 0) + text.count(s)
        text = _tokenize(text, secrets)
        data = text.encode("utf-8")
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        files.append({"name": name, "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest(), "content": text})

    # ① 四族 TSV：逐字节拷贝语义（脱敏后）；findings.tsv 缺席=fail-closed（调用侧）
    tables = {}
    for t in _FAMILY:
        rows = _read_rows(gd, t)
        if rows is None:
            if t == "findings.tsv":
                return None, None, (["findings.tsv 缺席（required 产物——账本未落发现表）"], {})
            warnings.append(t + " 缺席（mapper 静默降级面——不阻断导出）")
            continue
        tables[t] = rows
        emit(t, LF.join(rows) + LF if rows else "")

    fd_rows = tables.get("findings.tsv", [])
    ev_rows = tables.get("E-index.tsv", [])
    # ② EV/FD 卡：card_path 列为权威，缺省回落约定目录；basename 平铺（单段名律）
    ev_cells = [r.split(TAB) for r in ev_rows]
    fd_cells = [r.split(TAB) for r in fd_rows]
    cards, missing = 0, 0
    plan = []
    for r in ev_cells:
        cp = _cell(r, "E-index.tsv", "card_path") or (
            "evidence/" + _cell(r, "E-index.tsv", "id") + ".md")
        plan.append(cp)
    for r in fd_cells:
        cp = _cell(r, "findings.tsv", "card_path") or (
            "findings-cards/" + _cell(r, "findings.tsv", "id") + ".md")
        plan.append(cp)
    for cp in sorted(set(plan)):
        src = os.path.join(gd, cp)
        if os.path.isfile(src):
            with open(src, encoding="utf-8") as f:
                emit(os.path.basename(cp), f.read().replace("\r\n", LF))
            cards += 1
        else:
            missing += 1
            warnings.append("卡片缺席（mapper failures 侧记+TSV 兜底）: " + cp)
    # ③ battle-report.md（required pattern）
    emit("battle-report.md", _battle_report(gd, fd_cells, ev_rows, ts))

    ev_cards = sum(1 for f in files if f["name"].startswith("EV-") and f["name"].endswith(".md"))
    fd_cards = sum(1 for f in files if f["name"].startswith("FD-") and f["name"].endswith(".md"))
    counts = {
        "findings_rows": len(fd_rows),
        "findings_active": sum(1 for r in fd_cells
                               if _cell(r, "findings.tsv", "status") == "active"),
        "findings_superseded": sum(1 for r in fd_cells
                                   if _cell(r, "findings.tsv", "status") == "superseded"),
        "evidence_rows": len(ev_rows),
        "ev_cards": ev_cards, "fd_cards": fd_cards, "cards_missing": missing,
    }
    files.sort(key=lambda f: f["name"])
    return files, counts, (warnings, token_counts)


def _cookie_of(headers):
    """Set-Cookie 集中取 zl_sess 会话值（auth 中间件解 Cookie:zlstub 同名键）。"""
    for line in headers.get_all("Set-Cookie") or []:
        for part in line.split(","):
            kv = part.strip()
            if kv.startswith("zl_sess="):
                return kv.split(";", 1)[0]
    return None


def _post_json(url, payload, cookie=None, timeout=15):
    """POST JSON→(status, body_text, headers)。urllib 唯一网络出口（--push 专用径）。"""
    req = _urlreq.Request(url, data=json.dumps(payload).encode("utf-8"),
                          method="POST")
    req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8"), resp.headers
    except _urlreq.HTTPError as e:
        return e.code, e.read().decode("utf-8"), e.headers


def h_zhulong_export(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos:
        raise UsageError("zhulong-export 不收位置参数: " + " ".join(pos))
    for k in args:
        if k not in ("project-id", "object-id", "env-id", "out", "url", "timestamp", "push"):
            raise UsageError("zhulong-export 未知参数 --" + k)
    project_id = _int_arg(args, "project-id")
    object_id = _int_arg(args, "object-id") if args.get("object-id") not in (None, "") else None
    env_id = _int_arg(args, "env-id") if args.get("env-id") not in (None, "") else None
    push = args.get("push") is True
    base = (args.get("url") or os.environ.get("TANYIN_ZHULONG_URL") or DEFAULT_URL).rstrip("/")

    tl = _read_rows(goal_dir, "timeline.tsv") or []
    ts = args.get("timestamp") or (tl[-1].split(TAB)[0] if tl else "")
    out_dir = args.get("out") or os.path.join(goal_dir, PKG_DIR_NAME)
    out_dir = os.path.abspath(out_dir)
    # fail-closed：out 不得指向账本目录/含 13 表的目录（清理面会误删账本）
    _gd_abs = os.path.abspath(goal_dir)
    if out_dir == _gd_abs or any(os.path.isfile(os.path.join(out_dir, t)) for t in TABLES):
        raise UsageError("--out 不得指向账本 goal 目录（含 13 表）: " + out_dir)

    secrets = vault.secrets(goal_dir)
    files, counts, (warnings, token_counts) = build_package(goal_dir, out_dir, ts, secrets)
    if files is None:
        sys.stderr.write("FAIL " + warnings[0] + chr(10))
        return 1
    for w in warnings:
        sys.stderr.write("WARNING " + w + chr(10))

    pkg = {
        "kind": "tanyin-zhulong-import",
        "package_version": 1,
        "mode": "push" if push else "dry-run",
        "generated_at": ts,
        "goal_dir": os.path.abspath(goal_dir),
        "source_dir": out_dir,
        "url": base,
        "counts": counts,
        "redaction": {"vault_secrets": len(secrets), "token_counts": token_counts},
        "import_request": {
            "method": "POST",
            "endpoint": "/api/imports",
            "body": {"engineId": ENGINE_ID, "sourceDir": out_dir,
                     "projectId": project_id, "objectId": object_id, "envId": env_id},
        },
        "files": files,
    }
    with open(os.path.join(out_dir, PKG_JSON), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(pkg, ensure_ascii=False, indent=1) + LF)
    print("OK package %s (%d files)" % (out_dir, len(files)))
    print("OK json %s mode=%s" % (os.path.join(out_dir, PKG_JSON), pkg["mode"]))
    if not push:
        return 0

    # --push：登录→zl_sess→POST /api/imports（密值只走环境通道·不经 argv）
    user = os.environ.get("TANYIN_ZHULONG_USER")
    password = os.environ.get("TANYIN_ZHULONG_PASS")
    if not user or not password:
        raise UsageError("push 需要 TANYIN_ZHULONG_USER/TANYIN_ZHULONG_PASS 环境通道（密值不经 argv）")
    st, body, headers = _post_json(base + "/api/auth/login",
                                   {"username": user, "password": password})
    if st != 200:
        sys.stderr.write("FAIL login %s: %s" % (st, body.strip()[:300]) + chr(10))
        return 1
    cookie = _cookie_of(headers)
    if not cookie:
        sys.stderr.write("FAIL login 未下发 zl_sess 会话 Cookie" + chr(10))
        return 1
    print("OK login %s" % user)
    st, body, _h = _post_json(base + "/api/imports",
                              pkg["import_request"]["body"], cookie=cookie)
    if st != 201:
        sys.stderr.write("FAIL import %s: %s" % (st, body.strip()[:300]) + chr(10))
        return 1
    try:
        res = json.loads(body)
    except ValueError:
        sys.stderr.write("FAIL import 响应非 JSON: " + body.strip()[:300] + chr(10))
        return 1
    print("OK push taskId=%s stageCount=%s artifactCount=%s findingCount=%s failures=%s" % (
        res.get("taskId"), res.get("stageCount"), res.get("artifactCount"),
        res.get("findingCount"), len(res.get("failures") or [])))
    return 0


HANDLERS = {name: usage_guard(fn) for name, fn in {
    "zhulong-export": h_zhulong_export,
}.items()}
