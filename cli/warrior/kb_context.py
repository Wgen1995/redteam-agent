# -*- coding: utf-8 -*-
"""知识库上下文（VulnClaw kb_context 移植·战士化）。

哲学单源（.research/repos/VulnClaw/vulnclaw/agent/kb_context.py 只读参考）：
按当前需要把本地知识库的相关条目注入提示词，检索面永不炸主循环——任何
失败静默降级为空上下文（记日志不抛）；零命中=零注入。

战士化差异（对 diff 负责）：
- 语料=自有知识库技法卡 50 张（knowledge/concepts/CP-0001..0050，frontmatter
  元数据面），非 VulnClaw KB_DIR CVE/技巧混库；
- 关联信号=意图 title/detail+本意图 facts 行（VulnClaw 为 recon services+
  finding_types+user_input——同构：账本血缘信号替代其内存态信号）；
- 检索=确定性打分（无嵌入/无网络）：拉丁 token（非字母数字切分，≥2 字）+
  CJK 二元组，title×3/vuln_class×2/source_topic×2/applicability×1 分权，
  平分按卡 id 升序（可重放）；
- 降级面同源但收窄：无 i18n 门（本库纯中文语料，注入目标=模型上下文非
  UI）；会话级查询缓存不移植——R1 一意图一检索，模块级只缓存卡片索引
  （目录指纹键控的纯数据面缓存，非对话状态）；
- 新增 SKILL 按门路由瘦身（SKILL.md 路由表自己的执法：当前门→加载
  phases/<门>.md，单门单载，读完即用）：协议节=骨架保留+逐门详令节让位
  +phases/<门>.md duty 节单门单载；门未知/文件缺/duty 缺=原文回退。
"""
import os
import re

__all__ = ["load_cards", "retrieve", "build_kb_section", "gate_of",
           "slim_skill_by_gate"]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEFAULT_KB_DIR = os.path.join(REPO_ROOT, "knowledge", "concepts")
DEFAULT_PHASES_DIR = os.path.join(REPO_ROOT, "phases")

_GATE_RE = re.compile(r"^P\d+(?:\.\d+)?$")
_LATIN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+\-/]*")
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")

# 逐门详令节（duty 由 phases/<门>.md 单门单载，整册让位）
_GATE_ROUTED_HEADINGS = ("九门循环", "P3 演进循环")

# 字段分权（title 最强——卡名即意图词；applicability 最弱——泛化面）
_FIELD_WEIGHTS = (("title", 3), ("vuln_class", 2), ("source_topic", 2),
                  ("applicability", 1))

_CARD_CACHE = {}


# ---- 卡片语料面 ----

def _fingerprint(kb_dir):
    sig = []
    try:
        for name in sorted(os.listdir(kb_dir)):
            if not name.endswith(".md"):
                continue
            st = os.stat(os.path.join(kb_dir, name))
            sig.append((name, st.st_mtime_ns, st.st_size))
    except OSError:
        pass
    return tuple(sig)


def _parse_card(text):
    """flat frontmatter（--- 围栏内 key: value 行）→ dict。"""
    card = {}
    chunks = str(text or "").split("---", 2)
    body = chunks[1] if len(chunks) == 3 else ""
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        card[key.strip().lower()] = value.strip()
    return card


def load_cards(kb_dir=None):
    """载入技法卡（按 id 升序）。目录指纹缓存；任何失败降级为 []。"""
    d = kb_dir or DEFAULT_KB_DIR
    try:
        fp = _fingerprint(d)
    except OSError:
        return []
    cached = _CARD_CACHE.get(d)
    if cached is not None and cached[0] == fp:
        return list(cached[1])
    cards = []
    try:
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(d, name), encoding="utf-8") as f:
                card = _parse_card(f.read())
            if card.get("id") and card.get("title"):
                cards.append(card)
    except (OSError, ValueError):
        return []
    cards.sort(key=lambda c: c["id"])
    _CARD_CACHE[d] = (fp, cards)
    return list(cards)


# ---- 意图关联检索面（确定性）----

def _terms(text):
    """文本 → 术语集：拉丁 token（切分后≥2字，小写）+CJK 二元组。"""
    value = str(text or "").lower()
    terms = set()
    for run in _LATIN_RE.findall(value):
        for token in _TOKEN_RE.findall(run):
            if len(token) >= 2:
                terms.add(token)
    for run in _CJK_RUN_RE.findall(value):
        chars = list(run)
        if len(chars) == 1:
            terms.add(chars[0])
        for i in range(len(chars) - 1):
            terms.add("".join(chars[i:i + 2]))
    return terms


def retrieve(intent, extra_text="", top_k=3, kb_dir=None):
    """意图关联检索 → 命中卡列表（score>0；-score, id 确定性排序）。"""
    try:
        cards = load_cards(kb_dir)
        signal = " ".join([str(intent.get("title", "") or ""),
                           str(intent.get("detail", "") or ""),
                           str(extra_text or "")])
        signal_terms = _terms(signal)
        if not signal_terms:
            return []
        ranked = []
        for card in cards:
            score = 0
            for field, weight in _FIELD_WEIGHTS:
                value = card.get(field, "")
                if value:
                    score += weight * len(signal_terms & _terms(value))
            if score > 0:
                ranked.append((score, card["id"], card))
        ranked.sort(key=lambda t: (-t[0], t[1]))
        return [card for _, _, card in ranked[:max(1, int(top_k))]]
    except Exception:                           # noqa: BLE001 —— 降级律
        return []


def _clip(text, limit):
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def build_kb_section(intent, extra_text="", top_k=3, kb_dir=None):
    """格式化技法卡节（含「## 技法卡」头）。零命中/任何失败=空串。"""
    cards = retrieve(intent, extra_text=extra_text, top_k=top_k,
                     kb_dir=kb_dir)
    if not cards:
        return ""
    lines = ["## 技法卡（knowledge/concepts 按意图关联检索）",
             "以下技法卡来自本地知识库，按本意图关联检索，供参考使用：", ""]
    for card in cards:
        head = "- **%s · %s**" % (card.get("id", "?"), card.get("title", ""))
        if card.get("vuln_class"):
            head += "（%s）" % card["vuln_class"]
        lines.append(head)
        if card.get("applicability"):
            lines.append("  适用: %s" % _clip(card["applicability"], 160))
        if card.get("failure_modes"):
            lines.append("  转向: %s" % _clip(card["failure_modes"], 200))
    return "\n".join(lines)


# ---- 门路由面（SKILL 瘦身）----

def gate_of(goal_dir):
    """goal 当前门：timeline 末行 phase 列（P0/P3/P5.5 形）；无=空。"""
    try:
        from ledger.timeline import read_rows
        rows = read_rows(goal_dir)
    except Exception:                           # noqa: BLE001 —— 降级律
        return ""
    for row in reversed(rows):
        phase = (row[2] or "").strip() if len(row) > 2 else ""
        if _GATE_RE.match(phase):
            return phase
    return ""


def _duty_body(phase_text):
    """phases/<门>.md 的「## duty」节正文（至次个标题行——任意级 ##/###）。

    节级单载：duty 小节内的 ### 子节（如 P3 派发算分）仍留 phases 原文，
    按需再读——路由面=认知按需加载，不是整册搬运。"""
    lines = str(phase_text or "").splitlines()
    body, capture = [], False
    for line in lines:
        if line.startswith("##"):
            if capture:
                break
            capture = line.lstrip("#").strip().lower().startswith("duty")
            continue
        if capture:
            body.append(line)
    return "\n".join(body).strip()


def slim_skill_by_gate(skill_text, gate, phases_dir=None):
    """SKILL 按门路由瘦身：逐门详令节让位+phases/<门>.md duty 单门单载。

    回退律：门形不合法/phases 文件缺失/duty 节缺失 → 原文返回（不改不炸）。
    """
    text = str(skill_text or "")
    gate = (gate or "").strip()
    if not text or not _GATE_RE.match(gate):
        return text
    path = os.path.join(phases_dir or DEFAULT_PHASES_DIR, gate + ".md")
    try:
        with open(path, encoding="utf-8") as f:
            duty = _duty_body(f.read())
    except OSError:
        return text
    if not duty:
        return text
    blocks = re.split(r"(?m)^(?=## )", text)
    kept = [blocks[0]]
    for block in blocks[1:]:
        heading = block.splitlines()[0][3:].strip()
        if any(heading.startswith(drop)
               for drop in _GATE_ROUTED_HEADINGS):
            continue
        kept.append(block)
    slim = "".join(kept).rstrip("\n")
    slim += ("\n\n## 当前门详令（phases/%s.md 单门单载·duty）\n%s\n"
             % (gate, duty))
    return slim
