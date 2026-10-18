# -*- coding: utf-8 -*-
"""W5 知识环·知识注入回路（飞轮第 5 齿「注入」——入库存量接进战士简报）。

定位（docs/audits/2026-10-20-distill-registration-audit.md §八：注入回路尚未
接线=W5 知识环舰领地，本批 91 卡已是可消费存量）：把运行时库
$TANYIN_HOME/knowledge（技法 50 种子+21 蒸馏 + 避坑 20）按当前意图检索后
注入战士简报尾部——打仗时战士能用上相关卡，而不只是存量。

检索器（确定性，无嵌入无网络，kb_context 同律）：
- 输入=当前意图（类 kind/表面 surface/引擎 engine）+矩阵上下文
  （matrix.tsv 本意图行的 surface×vuln_class 族；无矩阵血缘时回退意图文本
  词扫描 + 引擎提示）；
- 技法卡按类簇匹配：卡 vuln_class wstg 族 ∩ 意图信号族；
- 避坑卡按漏报族匹配：卡 vuln_class 族 ∩ 信号族（miss 卡 source_topic
  带 GT 族）；同表面历史漏报族优先（卡文提及意图表面 → 加分）；
- 家族/CWE→wstg 词表单源复用 cli.knowledge.distill（FAMILY_TO_WSTG/
  CWE_TO_WSTG，禁本地复制防漂移）；
- 预算=每简报 ≤max_cards 张（缺省 5，可配），零命中=零注入不硬塞。

注入式参考裁定（docs/design/2026-10-20-graphled-master-verdict.md:104）：
注入=「供参考」——AI 是指挥官，卡是情报，打法自主；复用经验靠「放到眼前」
不靠「剥夺判断」。节面=卡片名+关键行+出处 CP 号（不整卡全文）。

审计：注入了哪几张进哪仗哪士 → goal 目录 kb-injections.tsv 追加审计行
（一卡一行；同意图同卡集幂等；仅活租约意图落审计——dry-run 面零写）。

开关：goal 配置 kb-inject.json（{"enabled": bool, "max_cards": int}，
enabled 缺省 true；坏 JSON 降级缺省——简报永不因配置炸，kb_context 降级律
同源）。装配接线=cli/warrior/context.py ContextBuilder.build()（简报装配
函数本体，loop.py:182 每回合经此组简报——舰船纪律：loop 冻结不碰）。

降级律（VulnClaw 移植同源）：检索/审计任何失败静默为空，绝不炸主循环。
"""
import datetime
import json
import os
import re
import time

from . import kb_context

__all__ = ["load_runtime_cards", "gather_signal", "retrieve",
           "build_section", "audit_injections", "load_config",
           "inject_briefing", "default_kb_root"]

DEFAULT_MAX_CARDS = 5            # 卡数帽：每简报 ≤5 张（防简报爆炸，可配）
CONFIG_NAME = "kb-inject.json"   # goal 配置开关（缺省开）
AUDIT_NAME = "kb-injections.tsv"  # goal 目录审计面（追加行）
_AUDIT_COLS = ("ts", "battle", "goal", "warrior", "intent_id", "card_id",
               "kind", "cluster", "source", "cards_sig")

# 引擎→类簇提示（词表证据：sqlmap=SQL 注入引擎（CWE-89）；deepex=凭据检查
# （CWE-798）+RCE 取证（CWE-94）派生面——均经 distill.CWE_TO_WSTG 同律映射）。
_ENGINE_HINTS = {"sqlmap": ("wstg-inpv",),
                 "deepex": ("wstg-conf", "wstg-inpv")}

_BATTLE_RE = re.compile(r"^battle-\d+$")
_FAMILY_TOKEN_RE = re.compile(r"wstg-[a-z]+")
_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

# 词表单源复用（cli.knowledge.distill 禁碰件=只读导入；导入失败降级空表——
# 矩阵列轴不依赖词表，文本扫描轴降级为零族=零注入，不炸简报）。
try:
    from knowledge import distill as _distill
    FAMILY_TO_WSTG = dict(_distill.FAMILY_TO_WSTG)
    CWE_TO_WSTG = dict(_distill.CWE_TO_WSTG)
except Exception:                                 # noqa: BLE001 —— 降级律
    FAMILY_TO_WSTG, CWE_TO_WSTG = {}, {}


def _iso(epoch):
    return datetime.datetime.fromtimestamp(
        float(epoch), datetime.timezone.utc).strftime(_ISO_FMT)


def default_kb_root():
    """运行时库根：$TANYIN_HOME（或 ~/.tanyin）/knowledge（battle.py BASE 同源）。"""
    home = os.environ.get("TANYIN_HOME") or os.path.join(
        os.path.expanduser("~"), ".tanyin")
    return os.path.join(home, "knowledge")


# ---------------------------------------------------------------- 语料面 --

# 模块级卡片索引缓存（目录指纹键控的纯数据面缓存，非对话状态——kb_context
# 同律：R1 一意图一检索不缓存查询结果，只缓存语料索引；指纹变=自动重载）。
_CARD_CACHE = {}


def _dir_fingerprint(d):
    sig = []
    try:
        for name in sorted(os.listdir(d)):
            if not name.endswith(".md"):
                continue
            st = os.stat(os.path.join(d, name))
            sig.append((name, st.st_mtime_ns, st.st_size))
    except OSError:
        pass
    return tuple(sig)


def load_runtime_cards(kb_root):
    """运行时库读面：(技法卡, 避坑卡) frontmatter 清单（id 升序；降级空）。

    技法=concepts/CP-*.md；避坑=negative/CP-*.md（write_negative_card 落形，
    读面与 scripts/capability_gate.read_negative_cards 同源字段——frontmatter
    flat 解析复用 kb_context._parse_card 单源）。
    """
    root = kb_root or default_kb_root()
    fps = tuple(_dir_fingerprint(os.path.join(root, sub))
                for sub in ("concepts", "negative"))
    cached = _CARD_CACHE.get(root)
    if cached is not None and cached[0] == fps:
        return (list(cached[1][0]), list(cached[1][1]))
    out = ([], [])
    for sub, kind, idx in (("concepts", "technique", 0),
                           ("negative", "negative", 1)):
        d = os.path.join(root, sub)
        try:
            names = sorted(n for n in os.listdir(d)
                          if n.startswith("CP-") and n.endswith(".md"))
        except OSError:
            continue
        for name in names:
            try:
                with open(os.path.join(d, name), encoding="utf-8",
                          errors="replace") as f:
                    card = kb_context._parse_card(f.read())
            except OSError:
                continue
            if card.get("id") and card.get("title"):
                card.setdefault("kind", kind)
                out[idx].append(card)
    _CARD_CACHE[root] = (fps, (out[0], out[1]))
    return (list(out[0]), list(out[1]))


# ---------------------------------------------------------------- 信号面 --

def families_of_vuln_class(vuln_class):
    """vuln_class → 族集（分号多值；冒号前缀=类簇轴；无冒号=整体一族）。"""
    fams = set()
    for token in str(vuln_class or "").split(";"):
        token = token.strip().lower()
        if token:
            fams.add(token.split(":", 1)[0])
    return fams


def families_from_text(text):
    """意图文本 → 信号族：词表族词边界匹配 + CWE 字面 + wstg-* 字面。"""
    value = str(text or "")
    low = value.lower()
    fams = set()
    for fam, wstg in sorted(FAMILY_TO_WSTG.items()):
        if re.search(r"\b%s\b" % re.escape(fam), low):
            fams.add(wstg)
    upper = value.upper()
    for cwe, wstg in sorted(CWE_TO_WSTG.items()):
        if cwe in upper:
            fams.add(wstg)
    fams.update(_FAMILY_TOKEN_RE.findall(low))
    return fams


def _intent_row(goal_dir, iid):
    """intents.tsv 该 id 的最新行（事件溯源后者覆盖前者）；缺/坏=空 dict。"""
    try:
        from ledger.core import Session
        row = None
        for r in Session(goal_dir).rows("intents.tsv"):
            if r and r[0] == iid:
                row = r
        if row is None:
            return {}
        return {"title": row[1], "detail": row[2], "status": row[3],
                "engine": row[4], "kind": row[5]}
    except Exception:                             # noqa: BLE001 —— 降级律
        return {}


def gather_signal(goal_dir, intent):
    """当前意图（类/表面/引擎）+矩阵上下文 → 检索信号。

    信号族来源（并集）：① matrix.tsv 本意图行（intent_id 列）的 vuln_class
    族+表面；② 无矩阵血缘时，意图文本提及的矩阵表面 → 该表面全部族；
    ③ 意图文本词扫描（词表/CWE/wstg 字面）；④ 引擎提示（_ENGINE_HINTS）。
    kind/engine 缺席时回读 intents.tsv 最新行（loop 传入 dict 自带）。
    """
    iid = str(intent.get("id", "") or "")
    row = _intent_row(goal_dir, iid)
    kind = str(intent.get("kind") or row.get("kind") or "")
    engine = str(intent.get("engine") or row.get("engine") or "")
    title = str(intent.get("title") or row.get("title") or "")
    detail = str(intent.get("detail") or row.get("detail") or "")

    matrix = []
    try:
        from ledger.core import Session
        matrix = [r for r in Session(goal_dir).rows("matrix.tsv")
                  if len(r) > 4]
    except Exception:                             # noqa: BLE001 —— 降级律
        matrix = []

    surfaces, families = set(), set()
    tied = [r for r in matrix if iid and r[4] == iid]
    for r in tied:
        if r[0]:
            surfaces.add(r[0])
        families |= families_of_vuln_class(r[1])
    if not tied:
        blob = title + " " + detail
        for r in matrix:
            if r[0] and r[0] in blob:
                surfaces.add(r[0])
                families |= families_of_vuln_class(r[1])
    families |= families_from_text(title + " " + detail)
    families.update(_ENGINE_HINTS.get(engine.strip().lower(), ()))
    families.discard("")

    text = " ".join([kind, engine, title, detail]
                    + sorted(surfaces) + sorted(families))
    return {"kind": kind, "engine": engine, "surfaces": sorted(surfaces),
            "families": sorted(families), "text": text}


# ---------------------------------------------------------------- 检索面 --

_FIELD_W_TECH = (("title", 3), ("vuln_class", 2), ("source_topic", 2),
                 ("applicability", 1))
_FIELD_W_NEG = (("title", 3), ("vuln_class", 2), ("failure_path", 1),
                ("conditions", 1))


def _lexical(card, signal_terms, fields):
    score = 0
    for field, weight in fields:
        value = card.get(field, "")
        if value:
            score += weight * len(signal_terms
                                  & kb_context._terms(value))
    return score


def _negative_subtype(source_topic):
    """source_topic → (子型, GT 族)：miss/<族> | fp | fact。"""
    topic = str(source_topic or "")
    m = re.search(r"/miss/([a-z0-9_-]+)$", topic)
    if m:
        return "miss", m.group(1)
    if topic.endswith("/fp"):
        return "fp", ""
    return "fact", ""


def retrieve(kb_root, signal, max_cards=DEFAULT_MAX_CARDS):
    """检索器：信号 → 相关卡引用集（确定性；零命中=[]；帽=max_cards）。"""
    try:
        techniques, negatives = load_runtime_cards(kb_root)
    except Exception:                             # noqa: BLE001 —— 降级律
        return []
    fam_sig = set(signal.get("families") or ())
    surfaces = set(signal.get("surfaces") or ())
    signal_terms = kb_context._terms(signal.get("text", ""))
    cap = max(0, int(max_cards))
    if cap == 0 or not (fam_sig or surfaces):
        return []

    ranked = []
    for card in techniques:
        inter = families_of_vuln_class(card.get("vuln_class")) & fam_sig
        if not inter:
            continue
        score = 3 * len(inter) + _lexical(card, signal_terms, _FIELD_W_TECH)
        ranked.append((score, card["id"], {
            "id": card["id"], "kind": "technique",
            "title": card.get("title", ""),
            "clusters": ",".join(sorted(inter)),
            "key_line": kb_context._clip(card.get("applicability"), 120),
            "source": card.get("source_topic") or card.get("source_id", ""),
            "score": score, "subtype": "", "gt_family": ""}))
    for card in negatives:
        inter = families_of_vuln_class(card.get("vuln_class")) & fam_sig
        blob = " ".join([card.get("title", ""), card.get("failure_path", ""),
                         card.get("conditions", "")])
        surf_hit = [s for s in surfaces if s and s in blob]
        if not inter and not surf_hit:
            continue
        subtype, gt_family = _negative_subtype(card.get("source_topic"))
        score = (3 * len(inter) + (4 if surf_hit else 0)
                 + _lexical(card, signal_terms, _FIELD_W_NEG))
        via = "+".join(([("族:" + ",".join(sorted(inter)))] if inter else [])
                       + ([("表面:" + ",".join(sorted(surf_hit)))]
                          if surf_hit else []))
        ranked.append((score, card["id"], {
            "id": card["id"], "kind": "negative",
            "title": card.get("title", ""),
            "clusters": ",".join(sorted(inter)),
            "via": via,
            "key_line": kb_context._clip(card.get("conditions"), 140),
            "source": card.get("source_id", ""),
            "score": score, "subtype": subtype, "gt_family": gt_family}))

    ranked.sort(key=lambda t: (-t[0], t[1]))
    return [ref for _, _, ref in ranked[:cap]]


# ---------------------------------------------------------------- 节面 --

def _neg_label(ref):
    label = {"miss": "漏报族", "fp": "重放证伪",
             "fact": "负面披露"}.get(ref.get("subtype"), "避坑")
    fam = ref.get("gt_family") or ""
    return "%s %s" % (label, fam) if fam else label


def build_section(selection):
    """卡集 → 简报尾节文本（名+关键行+出处 CP 号；不整卡全文；零集=空串）。"""
    if not selection:
        return ""
    lines = [
        "## 知识库参考（runtime 库按意图关联检索·供参考——"
        "AI 是指挥官，卡是情报，打法自主）",
        "以下卡片按本意图类簇/漏报族检索注入；仅情报参考，打法自主裁定。",
        ""]
    tech = [r for r in selection if r.get("kind") == "technique"]
    neg = [r for r in selection if r.get("kind") == "negative"]
    if tech:
        lines.append("### 相关打法")
        for r in tech:
            lines.append("- %s · %s [%s]" % (r["id"], r.get("title", ""),
                                             r.get("clusters", "")))
            if r.get("key_line"):
                lines.append("  适用: %s" % r["key_line"])
            if r.get("source"):
                lines.append("  出处: %s（CP 号 %s）" % (r["source"], r["id"]))
        lines.append("")
    if neg:
        lines.append("### 相关避坑")
        for r in neg:
            tag = "·".join(x for x in (_neg_label(r), r.get("clusters", ""))
                           if x)
            lines.append("- %s · %s [%s]" % (r["id"], r.get("title", ""), tag))
            if r.get("key_line"):
                lines.append("  要点: %s" % r["key_line"])
            if r.get("source"):
                lines.append("  出处: %s（CP 号 %s）" % (r["source"], r["id"]))
        lines.append("")
    lines.append("——需全文按 CP 号到知识库引用")
    return "\n".join(lines)


# ---------------------------------------------------------------- 审计面 --

def _battle_of(goal_dir):
    """goal 目录母目录名 battle-N 形=battle 名（运行时布局 battles/battle-N/G-rXX）。"""
    parent = os.path.basename(os.path.abspath(
        os.path.dirname(os.path.abspath(goal_dir))))
    return parent if _BATTLE_RE.match(parent) else ""


def _owner_of(goal_dir, iid):
    """活租约 owner（intents.tsv 最新行 detail 的 [owner:…] 标——write_cmds
    单源解析；无标/坏=空串=dry-run 面不落审计）。"""
    if not iid:
        return ""
    try:
        from ledger.write_cmds import lease_of_detail
        latest = None
        for r in _rows_raw(goal_dir, "intents.tsv"):
            if r and r[0] == iid:
                latest = r
        return lease_of_detail(latest[2] if latest else "")[0] or ""
    except Exception:                             # noqa: BLE001 —— 降级律
        return ""


def _rows_raw(goal_dir, tname):
    from ledger.core import Session
    return Session(goal_dir).rows(tname)


def audit_injections(goal_dir, battle, goal, warrior, intent_id, selection,
                     now=None):
    """注入审计：kb-injections.tsv 追加审计行（一卡一行；goal 锁内读查重）。

    幂等律：同意图同卡集（cards_sig）已落=零追加（build 每回合调用不翻倍）；
    卡集变=新审计组照落。返回本次追加行数。审计面是 sidecar 非链式账本，
    字段白空格折叠（防 TSV 断行）。
    """
    if not selection:
        return 0
    path = os.path.join(goal_dir, AUDIT_NAME)
    sig = ",".join(sorted(r["id"] for r in selection))
    ts = _iso(now() if callable(now) else (now or time.time()))
    new_rows = [[ts, str(battle or ""), str(goal or ""), str(warrior or ""),
                 str(intent_id or ""), r["id"], r.get("kind", ""),
                 kb_context._clip(r.get("clusters", "")
                                  or r.get("via", ""), 60),
                 kb_context._clip(r.get("source", ""), 80), sig]
                for r in selection]
    try:
        from ledger.filelock import goal_lock
        with goal_lock(goal_dir):
            existing = []
            if os.path.exists(path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    existing = [ln.split("\t")
                                for ln in f.read().splitlines() if ln.strip()]
            if any(len(r) > 9 and r[4] == intent_id and r[9] == sig
                   for r in existing):
                return 0
            with open(path, "a", encoding="utf-8", newline="\n") as f:
                if not existing:
                    f.write("\t".join(_AUDIT_COLS) + "\n")
                for r in new_rows:
                    f.write("\t".join(r) + "\n")
    except Exception:                             # noqa: BLE001 —— 降级律
        return 0
    return len(new_rows)


# ---------------------------------------------------------------- 配置面 --

def load_config(goal_dir):
    """goal 配置 kb-inject.json → {"enabled": bool, "max_cards": int}。

    缺文件=全缺省（默认开，帽 5）；坏 JSON/非对象/非法值=降级缺省——简报
    永不因配置炸（kb_context 降级律；与 planner.json fail-loud 分流：planner
    是操作员手写须拒启，注入是简报增强面宁可默认开）。
    """
    cfg = {"enabled": True, "max_cards": DEFAULT_MAX_CARDS}
    path = os.path.join(goal_dir, CONFIG_NAME)
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return cfg
    if not isinstance(raw, dict):
        return cfg
    if isinstance(raw.get("enabled"), bool):
        cfg["enabled"] = raw["enabled"]
    try:
        mc = int(raw.get("max_cards", DEFAULT_MAX_CARDS))
        if mc >= 0:
            cfg["max_cards"] = mc
    except (TypeError, ValueError):
        pass
    return cfg


# ---------------------------------------------------------------- 编排面 --

def inject_briefing(goal_dir, intent, kb_root=None, max_cards=None,
                     now=None):
    """装配编排：配置门 → 信号 → 检索 → 节文本 → 活租约审计。

    返回 (section_text, selection)。任何失败=("", [])（降级律，绝不炸简报）。
    审计门=意图已被领取（intents detail 带 [owner:…]）——dry-run 面
    （loop.dry_run 不领意图）组简报预览但零账写。
    """
    try:
        cfg = load_config(goal_dir)
        if not cfg["enabled"]:
            return ("", [])
        signal = gather_signal(goal_dir, intent)
        sel = retrieve(kb_root or default_kb_root(), signal,
                       cfg["max_cards"] if max_cards is None else max_cards)
        if not sel:
            return ("", [])
        section = build_section(sel)
        iid = str(intent.get("id", "") or "")
        owner = _owner_of(goal_dir, iid)
        if owner:
            audit_injections(goal_dir, _battle_of(goal_dir),
                             os.path.basename(os.path.abspath(goal_dir)),
                             owner, iid, sel, now=now)
        return (section, sel)
    except Exception:                             # noqa: BLE001 —— 降级律
        return ("", [])
