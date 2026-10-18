# -*- coding: utf-8 -*-
"""api_v2_tools（T7·工具执行页）——25 张工具卡只读面，路由
GET /api/v2/tools.json（?card=<名> 出单卡详情六节）。

舰间契约：本文件=本舰独写；只读投影零写入（一切文件 r 模式 open，禁
datetime.now，读输出确定性）；本页无写路径（只读+「复制调用命令」=页端
剪贴板动作，零服务端写）——POST_ROUTES 恒空。挂载=ROUTES 单源表由
include 机制（api_pages.py，UI-1 舰）分发——挂法钉在
tests/test_webui_pagespec_tools.py（_V2MountHandler）：GET 过会话门
（Handler._session_ok，缺会话=401 JSON）。

数据单源（spec §P8-P18 工具执行页）：
  卡清单 = cli/tools/cards.py 注册表（W3 蓝图 25 卡——名称/用途=summary/
           风险级 risk/档位 tier/revert 义务；as_public_dict 稳定投影，
           本层只加用途/收尾义务/可复制调用命令三个读面字段）；
  执行历史 = timeline 工具行（actor=tools：tool-card-exec name=… rc=… tier=…
           rate=… / tools-reject card=… ——tools.gate.execute 单源写方），
           多代合并（代自然序+文件序），新者在前，有界 200 行（超出如实
           标 truncated——不虚报全量，诚实法条）；
  单卡详情 = 六节（基本信息/用途/风险与审批/限速与拒绝清单/收尾义务/
           调用示例——示例命令 shlex 引用拼接，供页端「复制调用命令」）。
"""
import os
import shlex
import sys

_CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CLI_DIR not in sys.path:                     # server/测试同款兜底：cli/ 上 path
    sys.path.insert(0, _CLI_DIR)

from ledger import core                          # noqa: E402
from ledger.session_view import list_battles     # noqa: E402
from tools import cards as tool_cards            # noqa: E402  (25 卡注册表单源)

ROUTE_TOOLS = "/api/v2/tools.json"
ROUTES = {ROUTE_TOOLS: None}                     # 尾部赋真身（前向引用）
POST_ROUTES = {}                                 # 只读页：零写路由

HISTORY_LIMIT = 200                              # 执行史有界（诚实截断）
_TL = core.TABLES["timeline.tsv"]

SECTION_TITLES = (                               # 单卡详情六节（顺序即页面顺序）
    ("basics", "基本信息"),
    ("purpose", "用途"),
    ("risk", "风险与审批"),
    ("rate", "限速与拒绝清单"),
    ("revert", "收尾义务（revert）"),
    ("example", "调用示例"),
)


# ---------------------------------------------------------------- 通用小件 --

def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def _read_tsv_rows(path, nfields):
    text = _read_text(path)
    if text is None:
        return []
    out = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        cols = line.split("\t")
        out.append((cols + [""] * nfields)[:nfields] if len(cols) < nfields else cols)
    return out


def _gens(battle_dir):
    """G-* 子目自然序（G-r2<G-r10；server._latest_gen 同律）；无=空。"""
    try:
        names = [n for n in os.listdir(battle_dir)
                 if n.startswith("G-") and os.path.isdir(os.path.join(battle_dir, n))]
    except OSError:
        return []

    def key(name):
        digits = [int(d) for d in _digits(name)]
        return (digits or [0])[0]
    return sorted(names, key=key)


def _digits(name):
    out, cur = [], ""
    for ch in name:
        if ch.isdigit():
            cur += ch
        elif cur:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def _read_int(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("%s 需要 int/str/None，布尔无语义：%r" % (name, value))
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError("%s 无法解析为整数：%r" % (name, value))


def _resolve(battles_dir, battle, ledger_dir):
    """(battles, battle_meta|None, battle_dir) —— 有战用战，无战回落主账本。"""
    root = battles_dir if battles_dir is not None else ""
    battles = list_battles(root) if root else []
    if not battles:
        return [], None, str(ledger_dir or "")
    if battle is None:
        picked = battles[-1]
    else:
        n = _read_int(battle, "battle")
        picked = next((b for b in battles if b["n"] == n), None)
    if picked is None:
        return battles, None, None
    return battles, picked, os.path.join(root, picked["id"])


def _gen_dirs(battle_dir):
    gens = _gens(battle_dir)
    return [os.path.join(battle_dir, g) for g in gens] if gens else [battle_dir]


def _merged_tl(battle_dir):
    """timeline 多代合并（代自然序+文件序——tasks._merged_tl 同律）。"""
    rows = []
    for d in _gen_dirs(battle_dir):
        if not d:
            continue
        rows.extend(_read_tsv_rows(os.path.join(d, "timeline.tsv"), len(_TL)))
    return rows


# ---------------------------------------------------------------- 卡投影 --

def _card_dict(card):
    """注册表卡 → 读面投影（as_public_dict 稳定投影+三个读面字段）。"""
    d = card.as_public_dict()
    d["purpose"] = card.summary                    # 用途=summary 单源
    d["revert_required"] = card.has_revert_obligation
    d["example_command"] = shlex.join(list(card.example))   # 可复制调用命令
    return d


def _kv_pairs(pairs):
    out = []
    for label, value in pairs:
        if isinstance(value, (list, tuple)):
            value = " ".join(str(v) for v in value) if value else "—"
        out.append([label, str(value) if value not in ("", None) else "—"])
    return out


def _detail_sections(card):
    """单卡详情六节（key/标题/键值行——顺序=SECTION_TITLES 单源）。"""
    cmd = _card_dict(card)
    approval = ("是——L3 档未批即拒（审批绑定命令哈希）"
                if card.requires_approval else "否")
    deny = " ".join(card.deny_extra) if card.deny_extra else "无增补（全局拒绝清单之外）"
    flags = " ".join(card.rate_flags) if card.rate_flags else "无固化旗标"
    body = {
        "basics": _kv_pairs([
            ("名称", card.name), ("命令", card.binary), ("分组", card.category),
            ("卡册版本", card.version)]),
        "purpose": _kv_pairs([("用途", card.summary)]),
        "risk": _kv_pairs([
            ("风险级", card.risk), ("档位", card.tier),
            ("须逐次审批", approval)]),
        "rate": _kv_pairs([
            ("限速", card.rate), ("限速固化旗标", flags),
            ("卡黑名单增补", deny)]),
        "revert": _kv_pairs([
            ("收尾义务", card.revert),
            ("有无义务", "有——执行成功后须照卡核销" if card.has_revert_obligation
             else "无（只读卡显式声明）")]),
        "example": _kv_pairs([
            ("调用命令（可复制）", cmd["example_command"]),
            ("参数逐项", list(card.example))]),
    }
    return [{"key": k, "title": t, "items": body[k]} for k, t in SECTION_TITLES]


# ---------------------------------------------------------------- 执行史 --

def _parse_tool_event(event):
    """timeline 工具行事件 → dict|None（非本域形=None）。

    tool-card-exec name=X rc=N tier=T rate=R（gate.execute 成功面）；
    tools-reject card=X 原因…（卡层门拒面）。
    """
    if event.startswith("tool-card-exec "):
        flat = {}
        for part in event.split()[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                flat[k] = v
        if "name" not in flat:
            return None
        rc = flat.get("rc", "")
        try:
            rc = int(rc)
        except (TypeError, ValueError):
            pass
        return {"kind": "执行", "card": flat.get("name", ""), "rc": rc,
                "tier": flat.get("tier", ""), "rate": flat.get("rate", ""),
                "detail": ""}
    if event.startswith("tools-reject "):
        rest = event[len("tools-reject "):]
        card, detail = "", rest
        if rest.startswith("card="):
            head, _, tail = rest.partition(" ")
            card = head[len("card="):]
            detail = tail
        return {"kind": "拒绝", "card": card, "rc": None, "tier": "",
                "rate": "", "detail": " ".join(detail.split())}
    return None


def _tool_history(battle_dir, limit=HISTORY_LIMIT):
    """timeline 工具行 → 新者在前有界清单 + truncated 旗。"""
    picked, truncated = [], False
    for no, cols in enumerate(_merged_tl(battle_dir), 1):
        if (cols[1] or "").strip() != "tools":
            continue
        row = _parse_tool_event((cols[3] or "").strip())
        if row is None:
            continue
        row.update({"row": no, "ts": cols[0], "phase": cols[2],
                    "revert": cols[4]})
        picked.append(row)
    picked.reverse()                               # 新者在前
    if len(picked) > limit:
        picked, truncated = picked[:limit], True
    return picked, truncated


# ---------------------------------------------------------------- 读投影 --

def tools_view(battles_dir=None, battle=None, ledger_dir=None, card=None):
    """工具执行页读投影 → {battle, battles, cards, counts, history,
    history_truncated, note, detail?}；card=单卡详情六节（未知卡=error）。
    只读零写入。"""
    battles, meta, battle_dir = _resolve(battles_dir, battle, ledger_dir)
    if battles and meta is None:
        return {"error": "battle 不存在: %s" % _read_int(battle, "battle"),
                "battles": battles}

    cards = [_card_dict(c) for c in
             (tool_cards.get_card(n) for n in tool_cards.card_names())
             if c is not None]
    history, truncated = _tool_history(battle_dir)

    out = {
        "battle": ({"id": meta["id"], "n": meta["n"]} if meta else None),
        "battles": battles,
        "cards": cards,
        "counts": {
            "cards": len(cards),
            "tiers": {t: sum(1 for c in cards if c["tier"] == t)
                      for t in tool_cards.TIERS},
            "approval_required": sum(1 for c in cards if c["requires_approval"]),
            "revert_required": sum(1 for c in cards if c["revert_required"]),
            "exec": sum(1 for r in history if r["kind"] == "执行"),
            "reject": sum(1 for r in history if r["kind"] == "拒绝"),
        },
        "history": history,
        "history_truncated": truncated,
        "note": ("卡清单=cli/tools/cards.py 注册表单源（25 卡）；执行历史="
                 "timeline 工具行（actor=tools，新者在前，最近 %d 行）；"
                 "本页只读——「复制调用命令」为页端剪贴板动作。" % HISTORY_LIMIT),
    }
    if card is not None:
        picked = tool_cards.get_card(str(card))
        if picked is None:
            out["error"] = "工具卡不存在: %s（注册表 25 卡清单外）" % card
            return out
        out["detail"] = {"name": picked.name, "sections": _detail_sections(picked)}
    return out


# ---------------------------------------------------------------- 路由 --

def _tools_route(query, ledger_dir=None, battles_dir=None):
    try:
        payload = tools_view(battles_dir=battles_dir, battle=query.get("battle"),
                             ledger_dir=ledger_dir, card=query.get("card"))
    except ValueError as e:                           # 参数坏值=422
        return 422, {"error": "工具页参数无效: %s" % e}
    if "error" in payload:
        return 404, payload
    return 200, payload


ROUTES[ROUTE_TOOLS] = _tools_route


def dispatch(path, query, ledger_dir=None, battles_dir=None):
    """include 机制分发口 → (status, payload) | None(非本域路由)。"""
    fn = ROUTES.get(path)
    if fn is None:
        return None
    return fn(query, ledger_dir=ledger_dir, battles_dir=battles_dir)
