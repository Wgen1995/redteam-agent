# -*- coding: utf-8 -*-
"""api_v2_techniques（T6·P8-P18 技法库）——技法卡只读投影，路由 /api/v2/techniques.json。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，输出确定性——同输入两跑逐字节一致）；挂载=ROUTES 单源表由
include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_techniques.py（_V2MountHandler）：会话门复用
Handler._session_ok，缺会话=401 JSON。dispatch(path, query, ledger_dir,
battles_dir) 与 api_v2_broadcast 同形（本域不依赖账本参数，入参原样收下）。

数据单源（spec §P8-P18 技法库：50 卡列表+搜索+卡详情六节结构只读展示）：
  卡片    = knowledge/concepts/CP-*.md——YAML front matter（id/title/vuln_class/
            applicability/cost_hint/failure_modes/judgment/last_verified/status/
            source_id…）+ 六节正文（场景/步骤/工具引用/纪律标注/证据标准/边界）；
            早期 8 卡=四节旧构（适用条件/步骤/证据标准/边界（Boundaries））——
            shape 如实标「早期四节」，不硬凑六节（诚实法条）。
  索引    = knowledge/cp-index.tsv——source_topic/updated 联表补充。

搜索律（q）：子串命中 title/vuln_class/applicability/id（大小写不敏感）；
页端另做本地过滤，服务端全量只读给（50 卡量级=真全量）。

默认目录=仓根 knowledge（本文件上三级——与 metrics.default_repo_root 同构）；
concepts_dir/index_path 参数化可注入（测试夹具同源）。
"""
import os
import re

ROUTE_TECH = "/api/v2/techniques.json"
ROUTES = {ROUTE_TECH: None}                          # 尾部赋真身（前向引用）

_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_SECTION = re.compile(r"^## +(.+?)\s*$", re.M)
_KV = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
_CARD_FILE = re.compile(r"^CP-\d+\.md$")

# 六节规范序（六节结构=场景→步骤→工具引用→纪律标注→证据标准→边界）；
# 早期四节旧构节名照录其后（展示按卡内原序，shape 区分）。
SIX_SECTIONS = ("场景", "步骤", "工具引用", "纪律标注", "证据标准", "边界")
LEGACY_SECTIONS = ("适用条件", "边界（Boundaries）")


def _repo_root():
    """仓根=本文件（cli/webui/api_v2_techniques.py）上三级。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def default_concepts_dir():
    return os.path.join(_repo_root(), "knowledge", "concepts")


def default_index_path():
    return os.path.join(_repo_root(), "knowledge", "cp-index.tsv")


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _parse_front(text):
    """YAML front matter → dict（行式 key: value，零 yaml 依赖，3.9 纯 stdlib）。"""
    m = _FRONT.match(text)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        kv = _KV.match(line.strip())
        if kv:
            out[kv.group(1)] = kv.group(2).strip()
    return out or None


def _parse_sections(text):
    """正文 → [{name, body}]（## 节切分，节名剥净，body 收前后空白）。"""
    m = _FRONT.match(text)
    body = text[m.end():] if m else text
    marks = list(_SECTION.finditer(body))
    out = []
    for i, mm in enumerate(marks):
        start = mm.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out.append({"name": mm.group(1).strip(), "body": body[start:end].strip()})
    return out


def _shape_of(names):
    ordered = [n for n in names if n in SIX_SECTIONS]
    if len(ordered) == len(SIX_SECTIONS):
        return "六节"
    if any(n in LEGACY_SECTIONS for n in names):
        return "早期四节"
    return "节构不齐"


def _int_or_none(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _load_index(index_path):
    """cp-index.tsv → {id: row-dict}（首行表头；坏行跳过；缺文件=空表）。"""
    text = _read_text(index_path)
    if not text:
        return {}
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    head = lines[0].split("\t")
    out = {}
    for ln in lines[1:]:
        cols = ln.split("\t")
        row = {h: (cols[i] if i < len(cols) else "") for i, h in enumerate(head)}
        if row.get("id"):
            out[row["id"]] = row
    return out


def _card_summary(card, sections, idx_row):
    names = [s["name"] for s in sections]
    return {
        "id": card.get("id", ""),
        "title": card.get("title", ""),
        "kind": card.get("kind", ""),
        "vuln_class": card.get("vuln_class", ""),
        "applicability": card.get("applicability", ""),
        "cost_hint": _int_or_none(card.get("cost_hint")),
        "status": card.get("status", ""),
        "last_verified": card.get("last_verified", ""),
        "source_id": card.get("source_id", ""),
        "source_topic": (idx_row or {}).get("source_topic", card.get("source_topic", "")),
        "updated": (idx_row or {}).get("updated", ""),
        "section_names": names,
        "section_count": len(names),
        "shape": _shape_of(names),
    }


def techniques_view(q=None, id=None, concepts_dir=None, index_path=None):
    """技法库投影：缺省列表+搜索；给 id=单卡详情。只读零写入。"""
    cdir = concepts_dir if concepts_dir is not None else default_concepts_dir()
    ipath = index_path if index_path is not None else default_index_path()
    index = _load_index(ipath)
    cards = []
    details = {}
    try:
        names = sorted(n for n in os.listdir(cdir) if _CARD_FILE.match(n))
    except OSError:
        names = []
    for name in names:
        text = _read_text(os.path.join(cdir, name))
        if text is None:
            continue
        front = _parse_front(text)
        if not front or not front.get("id"):
            continue                                  # 坏卡=跳过（诚实跳过不造数）
        sections = _parse_sections(text)
        summary = _card_summary(front, sections, index.get(front["id"]))
        cards.append(summary)
        detail = dict(sorted(front.items()))     # front matter 键平铺（详情只读面）
        detail.update({
            "sections": sections,
            "section_names": [s["name"] for s in sections],
            "section_count": len(sections),
            "shape": summary["shape"],
        })
        details[front["id"]] = detail
    cards.sort(key=lambda c: c["id"])
    out = {
        "q": q or "",
        "id": id or "",
        "counts": {
            "total": len(cards),
            "six_section": sum(1 for c in cards if c["shape"] == "六节"),
            "legacy": sum(1 for c in cards if c["shape"] == "早期四节"),
        },
        "cards": cards,
    }
    if id:
        card = details.get(id)
        if card is None:
            return {"error": "技法卡不存在: %s（可搜 q 参数拿全量清单）" % id,
                    "id": id, "cards": [], "q": q or "",
                    "counts": out["counts"]}
        out["card"] = card
    if q:
        needle = str(q).strip().lower()
        if needle:
            out["cards"] = [c for c in cards if needle in (
                "%s %s %s %s" % (c["id"], c["title"], c["vuln_class"],
                                 c["applicability"])).lower()]
    return out


def _techniques_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = techniques_view(q=query.get("q") or None,
                                  id=query.get("id") or None)
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "技法库参数无效: %s" % e}
    return 200, payload


ROUTES[ROUTE_TECH] = _techniques_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
