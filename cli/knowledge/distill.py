# -*- coding: utf-8 -*-
"""蒸馏管线 v1（W5 知识环本体·设计 docs/design/evolution-flywheel-v1.md 第 2 齿）。

战后复盘→知识蒸馏：读 battle 结算数据（settle-report.txt + G-* 会话三表
findings/timeline/facts），LLM 离线态用**规则蒸馏 v1**（确定性纯函数，不调
真模型——宪法#43 第一性=找漏洞效果，规则先行把管线打通，模型道后补）：

  高置信模式 → 技法卡草案（cp 六列 id/title/source_id/source_topic/status/
               updated + 证据列）：同 CWE ≥2 例 verified 且带证据链=模式
               非巧合；
  失败路径   → 避坑卡草案（ng 扩列含 ledger_ref 出处——knowledge/negative/
               SCHEMA.md 必填九键），三路规则：
               ①误报路径：活发现被重放证伪（FD REJECTED / EV not-reproduced，
                 末值口径同 scripts/capability_gate.py fp_of_session）；
               ②漏报族：settle-report MISSING 按族（前缀）计数 ≥阈；
               ③负面披露：facts 不适用/未部署形（W3c 律负面结果已入 facts）。

草案纪律（棘轮门管入册）：蒸馏只落草案文件+人工确认位（review_status:
pending），**不自动写 cp-index/ng-index/negative/**——人工判读改 accept 后
走 confirm → scripts/capability_gate.py write_negative_card(knowledge_dir,
fields, body) 一函落卡（飞轮接口锚），knowledge/negative 变更由评测棘轮
CAPABILITY_SPECS.technique_cards 管住。种子库只读（R7）由写面自拒。

确定性：同输入两跑逐字节一致（日期锚=会话末行时间戳，非墙钟）。
退出码契约（CLI 面）：0=成 1=拒（草案未确认/校验不过）2=用法/环境。
"""
import importlib.util
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
GATE_PATH = os.path.join(REPO_ROOT, "scripts", "capability_gate.py")

_spec = importlib.util.spec_from_file_location("capability_gate_for_distill",
                                               GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class DistillError(Exception):
    """环境/用法错（目录不存在、非 battle-N 名形……）——CLI rc2。"""


class RejectError(Exception):
    """拒（草案未人工确认/非避坑草案/校验不过）——CLI rc1。"""


# ------------------------------------------------ 词表（固定小表·人工可改） --
# vuln_class=WSTG 词表键（knowledge/methodology/k1-baseline.tsv 单源键形）。
# 家族→WSTG：GT 类前缀（MISSING 行 id 去尾部 -NN）。
FAMILY_TO_WSTG = {
    "role": "wstg-authz", "idor": "wstg-authz", "authz": "wstg-authz",
    "hauth": "wstg-authn", "weakpass": "wstg-authn", "userenum": "wstg-authn",
    "jwt": "wstg-sess", "csrf": "wstg-sess", "session": "wstg-sess",
    "lfi": "wstg-inpv", "rfi": "wstg-inpv", "traversal": "wstg-inpv",
    "xxe": "wstg-inpv", "cmdi": "wstg-inpv", "sqli": "wstg-inpv",
    "ssti": "wstg-inpv", "deser": "wstg-inpv", "upload": "wstg-inpv",
    "ssrf": "wstg-inpv",
    "graphql": "wstg-apit", "ratelimit": "wstg-apit",
    "infoleak": "wstg-info", "cors": "wstg-conf",
    "redir": "wstg-clnt", "xss": "wstg-clnt",
}
# CWE→WSTG（发现 vuln_ref 列 AST-x+CWE-NN 形）。
CWE_TO_WSTG = {
    "CWE-639": "wstg-authz", "CWE-284": "wstg-authz", "CWE-862": "wstg-authz",
    "CWE-863": "wstg-authz", "CWE-285": "wstg-authz",
    "CWE-287": "wstg-authn", "CWE-521": "wstg-authn", "CWE-204": "wstg-authn",
    "CWE-347": "wstg-sess", "CWE-352": "wstg-sess",
    "CWE-89": "wstg-inpv", "CWE-78": "wstg-inpv", "CWE-22": "wstg-inpv",
    "CWE-98": "wstg-inpv", "CWE-94": "wstg-inpv", "CWE-434": "wstg-inpv",
    "CWE-502": "wstg-inpv", "CWE-1336": "wstg-inpv", "CWE-918": "wstg-inpv",
    "CWE-611": "wstg-inpv",
    "CWE-200": "wstg-info", "CWE-532": "wstg-info",
    "CWE-942": "wstg-conf", "CWE-798": "wstg-conf",
    "CWE-79": "wstg-clnt", "CWE-601": "wstg-clnt",
    "CWE-307": "wstg-apit",
}
# CWE→中文短名（技法卡草案 title 用；缺=用 CWE 号本身）。
CWE_ZH = {
    "CWE-639": "越权/IDOR", "CWE-79": "XSS 跨站脚本", "CWE-200": "信息暴露",
    "CWE-502": "反序列化", "CWE-918": "SSRF", "CWE-601": "开放重定向",
    "CWE-521": "弱口令", "CWE-22": "路径穿越", "CWE-89": "SQL 注入",
    "CWE-284": "访问控制", "CWE-942": "CORS 配置", "CWE-1336": "SSTI",
    "CWE-307": "限流缺失", "CWE-98": "文件包含", "CWE-434": "危险上传",
    "CWE-78": "命令注入", "CWE-611": "XXE", "CWE-287": "认证缺陷",
    "CWE-798": "硬编码凭据", "CWE-94": "代码注入", "CWE-204": "用户枚举差异",
    "CWE-862": "授权缺失", "CWE-863": "授权不当", "CWE-347": "JWT 签名缺失",
    "CWE-352": "CSRF", "CWE-285": "授权不当", "CWE-532": "敏感信息泄露",
}
FALLBACK_WSTG = "wstg-busl"  # 兜底=人工判读桶（k1 rationale 本就「人工为主」）
# facts 负面披露标记（W3c 律：负面结果入 facts——多字符标记防误吃普通 info）。
NEG_FACT_MARKERS = ("不适用", "未部署", "不存在", "未发现", "无法", "不可达",
                    "无解", "拒绝", "失败")

_BATTLE_RE = re.compile(r"^battle-(\d+)$")
_CWE_RE = re.compile(r"CWE-\d+")
_RECALL_RE = re.compile(r"^recall=([0-9.]+) \((\d+)/(\d+)\)")
_MISSING_RE = re.compile(r"^MISSING\t(\S+)")
_REPLAY_RE = re.compile(r"^replay:(\S+?):(VERIFIED|REPAIRED|REJECTED)")
_PROBE_RE = re.compile(r"replay-probe (\S+) verdict=(\S+)")
_NOTE_RE = re.compile(r"note=(.*)$")

# 账本冻结列位（schemas.py TABLES 单源；真实会话无表头——同 gate 契约锚）。
_FI_ID, _FI_TITLE, _FI_EXPLOIT, _FI_VULNREF = 0, 2, 5, 8
_FI_EV, _FI_CEV, _FI_STATUS = 13, 14, 16
_TI_EVENT = 3
_FINDINGS_W, _TIMELINE_W, _FACTS_W = 19, 8, 8
_FT_KIND, _FT_TARGET, _FT_DETAIL = 2, 3, 4

MAX_TITLE = 60


def _read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_front(text):
    """front matter KV 平铺（gate._parse_front 同款窄面，单源不重写语义）。"""
    return gate._parse_front(text)  # noqa: SLF001  同仓件内部窄面（锚接口）


# ======================================================== battle 装载 ==

def _read_table_lines(path):
    """账本表读 → [{...列, line:物理行号}]（1 基；表头行让行不进数据集）。

    行号=ledger_ref 锚（battle-N/<表>.tsv:<line> 指回物理行——可回放核验律：
    指到的物理行真含那条数据）。无表头=真实 battle 会话主形；带表头=夹具/
    新工具产形同吃（首列==列名即让行，行号随物理序不漂）。
    """
    try:
        lines = [ln for ln in _read_text(path).splitlines() if ln.strip()]
    except OSError:
        return []
    out = []
    for i, ln in enumerate(lines):
        cols = ln.split("\t")
        if i == 0 and cols and cols[0] in ("id", "timestamp", "attack_surface"):
            continue
        out.append({"cols": cols, "line": i + 1})
    return out


def _gen_of(home):
    """battle 目录内 G-* 会话主代优选（gate._gen_of 同律：首数字+名字典序，
    主代排备份族前——G-r30 先于 G-r30.bak-preReplay）。缺=None。"""
    try:
        names = [n for n in os.listdir(home) if n.startswith("G-")
                 and os.path.isdir(os.path.join(home, n))]
    except OSError:
        return None

    def key(name):
        ds = [int(d) for d in re.findall(r"\d+", name)]
        return ((ds or [0])[0], name)
    return sorted(names, key=key)[0] if names else None


def _parse_settle(path):
    """settle-report.txt → (settled, recall, hits, total, missing 清单)。"""
    try:
        text = _read_text(path)
    except OSError:
        return False, None, None, None, []
    recall, hits, total, missing = None, None, None, []
    for ln in text.splitlines():
        m = _RECALL_RE.match(ln.strip())
        if m:
            recall, hits, total = float(m.group(1)), int(m.group(2)), int(m.group(3))
            continue
        m2 = _MISSING_RE.match(ln)
        if m2:
            missing.append(m2.group(1))
    return True, recall, hits, total, missing


def load_battle(battle_dir):
    r"""battle 家目录装载 → 蒸馏输入包（纯读，零写入）。

    布局=<suite>/battle-N/（名形 battle-\d+）+G-<gen>/（主代会话）+
    settle-report.txt（可缺=未结算，诚实标注不造数）。
    """
    bd = os.path.abspath(battle_dir)
    name = os.path.basename(bd)
    if not _BATTLE_RE.match(name):
        raise DistillError("目录名须为 battle-N 形: %s" % name)
    if not os.path.isdir(bd):
        raise DistillError("battle 目录不存在: %s" % bd)
    gen = _gen_of(bd)
    settled, recall, hits, total, missing = _parse_settle(
        os.path.join(bd, "settle-report.txt"))
    bat = {"name": name, "dir": bd, "gen": gen,
           "session": os.path.join(bd, gen) if gen else None,
           "settled": settled, "recall": recall, "recall_hits": hits,
           "recall_total": total, "missing": missing,
           "findings": [], "timeline": [], "facts": [], "last_ts": None}
    if not gen:
        return bat
    bat["findings"] = _findings_rows(bd, gen)
    bat["timeline"] = _timeline_rows(bd, gen)
    bat["facts"] = _facts_rows(bd, gen)
    if bat["timeline"]:
        bat["last_ts"] = bat["timeline"][-1]["ts"]
    return bat


def _findings_rows(bd, gen):
    rows = _read_table_lines(os.path.join(bd, gen, "findings.tsv"))
    return [{"id": (r["cols"][_FI_ID] if len(r["cols"]) > _FI_ID else ""),
             "title": (r["cols"][_FI_TITLE] if len(r["cols"]) > _FI_TITLE else ""),
             "exploit": (r["cols"][_FI_EXPLOIT] if len(r["cols"]) > _FI_EXPLOIT else ""),
             "vuln_ref": (r["cols"][_FI_VULNREF] if len(r["cols"]) > _FI_VULNREF else ""),
             "evidence_ids": (r["cols"][_FI_EV] if len(r["cols"]) > _FI_EV else ""),
             "control_evidence_ids": (r["cols"][_FI_CEV] if len(r["cols"]) > _FI_CEV else ""),
             "status": (r["cols"][_FI_STATUS] if len(r["cols"]) > _FI_STATUS else ""),
             "line": r["line"], "w": len(r["cols"])}
            for r in rows if len(r["cols"]) == _FINDINGS_W]


def _timeline_rows(bd, gen):
    rows = _read_table_lines(os.path.join(bd, gen, "timeline.tsv"))
    return [{"event": (r["cols"][_TI_EVENT] if len(r["cols"]) > _TI_EVENT else ""),
             "ts": (r["cols"][0] if r["cols"] else ""), "line": r["line"],
             "w": len(r["cols"])}
            for r in rows if len(r["cols"]) == _TIMELINE_W]


def _facts_rows(bd, gen):
    rows = _read_table_lines(os.path.join(bd, gen, "facts.tsv"))
    return [{"id": (r["cols"][0] if r["cols"] else ""),
             "kind": (r["cols"][_FT_KIND] if len(r["cols"]) > _FT_KIND else ""),
             "target": (r["cols"][_FT_TARGET] if len(r["cols"]) > _FT_TARGET else ""),
             "detail": (r["cols"][_FT_DETAIL] if len(r["cols"]) > _FT_DETAIL else ""),
             "line": r["line"], "w": len(r["cols"])}
            for r in rows if len(r["cols"]) == _FACTS_W]


# ======================================================== 规则蒸馏 v1 ==

def _latest_by_id(findings):
    """supersede 流：同 FD id 多行取末值行（gate fp 面同口径）。"""
    latest = {}
    for r in findings:
        latest[r["id"]] = r
    return latest


def _replay_states(timeline):
    """timeline 事件溯源末值（G-52 同证据基）→ (fd_state, ev_state, probe, notes)。"""
    fd_state, ev_state, probe, notes = {}, {}, {}, {}
    for r in timeline:
        ev = r["event"]
        m = _REPLAY_RE.match(ev)
        if m:
            rid, verdict = m.group(1), m.group(2)
            nm = _NOTE_RE.search(ev)
            notes[rid] = nm.group(1) if nm else ""
            if rid.startswith("FD-"):
                fd_state[rid] = verdict
            else:
                ev_state[rid] = verdict
        m2 = _PROBE_RE.search(ev)
        if m2:
            probe[m2.group(1)] = m2.group(2)
    return fd_state, ev_state, probe, notes


def falsified_findings(bat):
    """误报面：活发现集内重放证伪 → [{row, signal, note}]（一发现一信号不双计）。"""
    latest = _latest_by_id(bat["findings"])
    active = [r for r in latest.values() if r["status"] in ("", "active")]
    fd_state, ev_state, probe, notes = _replay_states(bat["timeline"])
    blocked = {i for i, v in probe.items() if v == "not-reproduced"}
    blocked |= {i for i, v in ev_state.items() if v == "REJECTED"}
    out = []
    for r in sorted(active, key=lambda x: x["id"]):
        evs = [x for x in (r["evidence_ids"] + ";" + r["control_evidence_ids"]).split(";") if x]
        if fd_state.get(r["id"]) == "REJECTED":
            out.append({"row": r, "signal": "FD 重放末值=REJECTED",
                        "note": (notes.get(r["id"]) or "").strip()})
        elif any(e in blocked for e in evs):
            hit = next(e for e in evs if e in blocked)
            why = ("EV 重放 REJECTED" if ev_state.get(hit) == "REJECTED"
                   else "EV 重放探针 not-reproduced")
            out.append({"row": r, "signal": "%s（%s）" % (why, hit),
                        "note": (notes.get(hit) or "").strip()})
    return out


def technique_patterns(bat, min_pattern=2):
    """高置信模式：同 CWE 的活+verified+带证据发现 ≥min_pattern 例 → 分组。"""
    latest = _latest_by_id(bat["findings"])
    groups = {}
    for r in latest.values():
        if r["status"] not in ("", "active"):
            continue
        if r["exploit"] != "verified" or not r["evidence_ids"].strip():
            continue
        m = _CWE_RE.search(r["vuln_ref"])
        if not m:
            continue  # 无 CWE 不猜（人工判读位）
        groups.setdefault(m.group(0), []).append(r)
    return {c: rows for c, rows in groups.items() if len(rows) >= min_pattern}


def missing_families(bat, min_miss=2):
    """漏报族：settle MISSING 按 GT 类前缀（去尾 -NN）计数 ≥min_miss。"""
    fams = {}
    for mid in bat["missing"]:
        fam = mid.rsplit("-", 1)[0]
        fams.setdefault(fam, []).append(mid)
    return {f: ids for f, ids in sorted(fams.items()) if len(ids) >= min_miss}


def negative_facts(bat):
    """负面披露：facts 不适用/未部署形（W3c 律负面结果接上蒸馏层）。

    两类样板不成卡（真数据 20 战校准——人审队列不被刷屏）：
      canary:*/asset-class:* 元披露=靶场口径样板（每战复读）；
      「负结果置态」=submatrix 逐端点×类系统生成闭包（每战数十行）。
    跳过计数经 skipped 记因（诚实披露不静默）。"""
    kept, dropped = [], 0
    for r in bat["facts"]:
        if r["kind"] != "info" or not any(m in r["detail"] for m in NEG_FACT_MARKERS):
            continue
        if (r["target"].startswith("canary:")
                or r["target"].startswith("asset-class:")
                or "负结果置态" in r["detail"]):
            dropped += 1
            continue
        kept.append(r)
    bat["_fact_meta_skipped"] = dropped
    return kept


def sentinel_rule_drafts(bat, date=None):
    """K6 误报回流（功能11补件一）：重放证伪教训 → 哨兵规则草稿行。

    确定性纯函数（零写入）：每条被重放证伪的活发现产一行草稿——
    signal_pattern=标题首段（冒号/括号前）regex escape（同形误报的识别词），
    action=mark-suspicious（保守默认，人工并入时可改），note=ledger_ref+
    证伪信号+重放 note。草稿落 distill 产物区 sentinel-staging/ 待人工，
    不自动合入 knowledge/engineering/sentinels-v1.tsv——合入须人工
    bump version（规则文件版本化纪律，飞轮 K6 齿）。
    """
    rows = []
    for f in falsified_findings(bat):
        r = f["row"]
        core = re.split(r"[：:（(]", (r["title"] or "").strip(), 1)[0].strip()
        core = _clip(core, 24) or r["id"]
        m = _CWE_RE.search(r["vuln_ref"] or "")
        vref = m.group(0) if m else ((r["vuln_ref"] or "").strip() or "未知域")
        note = ("；重放 note=%s" % _clip(f["note"], 60)) if f["note"] else ""
        rows.append({
            "id": "SEN-D-%03d" % (len(rows) + 1),
            "signal_pattern": "(?i)" + re.escape(core),
            "judge": "title 含『%s』且 vuln_ref=%s 的发现报 verified 前——先重放复验再报"
                     % (core, vref),
            "action": "mark-suspicious",
            "note": "K6 回流草稿（distill/%s·%s）: findings.tsv:%d %s『%s』被重放证伪"
                    "（%s%s）——人工确认可泛化后并入 knowledge/engineering/"
                    "sentinels-v1.tsv 并 bump version 方生效"
                    % (bat["name"], date or _date_anchor(bat), r["line"], r["id"],
                       _clip(r["title"], 40), f["signal"], note),
        })
    return rows


def _sentinel_draft_tsv(name, rows):
    """哨兵草稿 TSV 文本（首行 version: draft=未生效标记；单元格去制表/换行）。"""
    NL, TAB = chr(10), chr(9)
    head = NL.join((
        "# version: draft（K6 回流草稿——未生效，不合入 "
        "knowledge/engineering/sentinels-v1.tsv 不算数）",
        "# source: distill/%s（误报教训→哨兵规则草稿钩子·功能11补件一）" % name,
        "# 人工确认位: 逐条核 signal_pattern 可泛化（非单靶巧合、非环境态偶发）"
        "→手工并入规则文件并 bump version",
    ))
    cols = ("id", "signal_pattern", "judge", "action", "note")
    lines = [head, TAB.join(cols)]
    for row in rows:
        lines.append(TAB.join(
            str(row[k]).replace(TAB, " ").replace(chr(13), " ").replace(NL, " ")
            for k in cols))
    return NL.join(lines) + NL



# ======================================================== 草案落盘 ==

def _atomic_write(path, text):
    gate._atomic_write(path, text)  # noqa: SLF001  同仓件原子写窄面（锚接口）


def _front(fields):
    return "---\n" + "".join("%s: %s\n" % (k, fields[k]) for k in fields) + "---\n"


def _clip(text, n):
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= n else text[:n - 1] + "…"


def _safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.\-]", "_", s)


def _date_anchor(bat, today=None):
    """确定性日期锚=会话末行时间戳日期（非墙钟）；无会话数据=今天参数兜底。"""
    if today:
        return today
    if bat["last_ts"]:
        return bat["last_ts"][:10]
    if bat["timeline"]:
        return bat["timeline"][-1]["ts"][:10]
    return "1970-01-01"


CONFIRM_SECTION = """
## 人工确认位
> 蒸馏=规则 v1 草案，未经人工判读不得入册（评测棘轮门管入册，不自动进
> cp-index/ng-index）。逐条勾完再改 review_status。
- [ ] 模式/坑真实可复用（非单靶巧合、非环境态偶发）
- [ ] 出处行号回读核验过（ledger_ref 指到的物理行真含该数据）
- [ ] title/conditions 措辞与存量卡不重复（similar_existing 对过）
- 确认：把 review_status: pending 改成 accept，再走
  python3 -m cli.knowledge confirm <本文件> --knowledge-dir <运行时库> --reviewer <名>
"""


def _next_preview_id(knowledge_dir):
    """编号预演=CP 家族跨索引连续（cp-index ∪ ng-index max+1；只读不分配）。"""
    if not knowledge_dir or not os.path.isdir(knowledge_dir):
        return "CP-0001"
    return gate.next_negative_id(knowledge_dir)


def _similar_existing(knowledge_dir, keyword):
    """存量卡重叠提示（title 含关键词的 cp-index id——人工去重参考，只读）。"""
    if not knowledge_dir or not keyword:
        return ""
    idx = os.path.join(knowledge_dir, "cp-index.tsv")
    rows = gate.read_index_family(idx)
    hits = [r["id"] for r in rows if keyword in (r.get("title") or "")]
    return ",".join(hits[:8])


def distill_battle(battle_dir, out=None, knowledge_dir=None, min_pattern=2,
                   min_miss=2, today=None):
    """一战蒸馏 → 草案文件+报告（纯 out 目录写入；knowledge 只读）。

    产物：<out>/techniques/CP-XXXX--technique-*.md（cp 六列+证据列）、
    <out>/pitfalls/CP-XXXX--pitfall-{fp,miss,fact}-*.md（ng 扩列含
    ledger_ref）、<out>/distill-report.json。缺省 out=<battle-dir>/distill。
    """
    bat = load_battle(battle_dir)
    name = bat["name"]
    out = os.path.abspath(out or os.path.join(bat["dir"], "distill"))
    tdir, pdir = os.path.join(out, "techniques"), os.path.join(out, "pitfalls")
    _clean_stale_drafts(tdir, "technique")
    _clean_stale_drafts(pdir, "pitfall")
    drafts, skipped = [], []
    date = _date_anchor(bat, today)
    counter = _Counter(_next_preview_id(knowledge_dir))
    if not bat["gen"]:
        skipped.append({"rule": "all",
                        "reason": "no-session：会话三表缺席（directive-only 战），"
                                  "规则蒸馏无数据面，零产出不造卡"})

    # ① 高置信模式 → 技法卡草案（cp 六列）
    for cwe, rows in sorted(technique_patterns(bat, min_pattern).items()):
        zh = CWE_ZH.get(cwe, cwe)
        title = _clip("%s %s 高置信打法（%s·%d 例全验证）"
                      % (cwe, zh, name, len(rows)), MAX_TITLE)
        fd_refs = ",".join(r["id"] for r in sorted(rows, key=lambda x: x["id"]))
        similar = _similar_existing(knowledge_dir, zh)
        pid = counter.next()
        fields = [
            ("id", pid), ("kind", "technique-draft"), ("title", title),
            ("source_id", name), ("source_topic", "distill/%s/%s" % (name, cwe)),
            ("status", "draft"), ("updated", date),
            ("vuln_class", CWE_TO_WSTG.get(cwe, FALLBACK_WSTG)),
            ("evidence_count", str(len(rows))), ("fd_refs", fd_refs),
            ("confidence_basis",
             "rule-v1：同 CWE ≥%d 例 verified 且各带证据链（末值行）" % min_pattern),
            ("review_status", "pending"),
        ]
        if similar:
            fields.append(("similar_existing", similar))
        body = ("## 模式\n%s 战中发现 %d 例同域 verified 发现（各带证据链），"
                "构成可复用打法候选。\n\n## 证据\n" % (name, len(rows))
                + "".join("- %s（findings.tsv:%d）%s\n"
                          % (r["id"], r["line"], _clip(r["title"], 50))
                          for r in sorted(rows, key=lambda x: x["id"]))
                + "\n> id=预演号（跨索引连续只读推演），入册时由写面重分配。\n"
                + CONFIRM_SECTION)
        path = os.path.join(tdir, "%s--technique-%s.md" % (pid, _safe_name(cwe)))
        _atomic_write(path, _front(dict(fields)) + "\n" + body)
        drafts.append({"file": os.path.relpath(path, out), "path": path,
                       "kind": "technique", "id_preview": pid, "title": title})

    # ② 误报路径 → 避坑卡草案（ledger_ref=findings 行号）
    for f in falsified_findings(bat):
        r = f["row"]
        cwe = _CWE_RE.search(r["vuln_ref"])
        cwe = cwe.group(0) if cwe else ""
        note = ("；重放 note=%s" % _clip(f["note"], 80)) if f["note"] else ""
        pid = counter.next()
        fields = {
            "id": pid, "kind": "negative",
            "title": _clip("重放证伪：%s" % _clip(r["title"], 40), MAX_TITLE),
            "failure_path": "发现 %s『%s』判 verified 后被重放证伪（%s%s）"
                            % (r["id"], _clip(r["title"], 40), f["signal"], note),
            "conditions": "同判定通道（vuln_ref=%s+同证据形态）再出『verified』"
                          "结论时——先重放复验再报；note 所指环境态差异重现即适用"
                          % (cwe or "未知域"),
            "ledger_ref": "%s/findings.tsv:%d" % (name, r["line"]),
            "vuln_class": CWE_TO_WSTG.get(cwe, FALLBACK_WSTG),
            "status": "learned", "last_verified": date,
            "source_id": name, "source_topic": "distill/%s/fp" % name,
            "review_status": "pending",
        }
        body = ("## 失败路径\n%s\n\n## 触发条件\n%s\n\n## 出处\n%s"
                "（回读该行即见 FD 行本体；timeline 末值口径）\n"
                % (fields["failure_path"], fields["conditions"],
                   fields["ledger_ref"]) + CONFIRM_SECTION)
        path = os.path.join(pdir, "%s--pitfall-fp-%s.md" % (pid, _safe_name(r["id"])))
        _atomic_write(path, _front(_order_fields(fields)) + "\n" + body)
        drafts.append({"file": os.path.relpath(path, out), "path": path,
                       "kind": "pitfall-fp", "id_preview": pid,
                       "title": fields["title"]})

    # ③ 漏报族 → 避坑卡草案（ledger_ref=timeline 末行=战末见证）
    fams = missing_families(bat, min_miss)
    if bat["missing"] and not bat["timeline"]:
        skipped.append({"rule": "missing-family",
                        "reason": "no-session-anchor：无 timeline 行可锚（诚实跳过不造卡）"})
        fams = {}
    for fam, ids in fams.items():
        pid = counter.next()
        fields = {
            "id": pid, "kind": "negative",
            "title": _clip("漏报族 %s：%s 全战 %d 条缺" % (fam, name, len(ids)), MAX_TITLE),
            "failure_path": "GT 类 %s 共 %d 条全缺（recall=%s）——该通道未铺开或"
                            "未深入，非靶面无此窟" % (fam, len(ids),
                                                      bat["recall"] if bat["recall"] is not None else "?"),
            "conditions": "同靶型同窗口再战时——先核 %s 通道是否铺面；已铺仍缺="
                          "深挖不足（字典/意图面问题）" % fam,
            "ledger_ref": "%s/timeline.tsv:%d" % (name, bat["timeline"][-1]["line"]),
            "vuln_class": FAMILY_TO_WSTG.get(fam, FALLBACK_WSTG),
            "status": "learned", "last_verified": date,
            "source_id": name, "source_topic": "distill/%s/miss/%s" % (name, fam),
            "review_status": "pending",
        }
        body = ("## 失败路径\n%s\n\n## 触发条件\n%s\n\n## 出处\n%s"
                "（战末行见证：全战无该族 FD）\n\n全缺清单：%s\n"
                % (fields["failure_path"], fields["conditions"],
                   fields["ledger_ref"], ",".join(ids)) + CONFIRM_SECTION)
        path = os.path.join(pdir, "%s--pitfall-miss-%s.md" % (pid, _safe_name(fam)))
        _atomic_write(path, _front(_order_fields(fields)) + "\n" + body)
        drafts.append({"file": os.path.relpath(path, out), "path": path,
                       "kind": "pitfall-miss", "id_preview": pid,
                       "title": fields["title"]})

    # ④ 负面披露 → 避坑卡草案（ledger_ref=facts 行号）
    neg_fact_rows = negative_facts(bat)
    if bat.get("_fact_meta_skipped"):
        skipped.append({"rule": "negative-fact",
                        "reason": "meta/submatrix 样板 %d 行不成卡（canary:/"
                                  "asset-class: 元披露+负结果置态闭包）"
                                  % bat["_fact_meta_skipped"]})
    for fr in neg_fact_rows:
        pid = counter.next()
        fields = {
            "id": pid, "kind": "negative",
            "title": _clip("负面披露：%s" % _clip(fr["detail"], 40), MAX_TITLE),
            "failure_path": "facts 在案负面结果：%s" % _clip(fr["detail"], 160),
            "conditions": "同部署形态/同靶型时——排兵前先读 facts 披露，别把已知"
                          "不通的路再走一遍（target=%s）" % fr["target"],
            "ledger_ref": "%s/facts.tsv:%d" % (name, fr["line"]),
            "vuln_class": "wstg-info",
            "status": "learned", "last_verified": date,
            "source_id": name, "source_topic": "distill/%s/fact" % name,
            "review_status": "pending",
        }
        body = ("## 失败路径\n%s\n\n## 触发条件\n%s\n\n## 出处\n%s"
                "（回读该行即见 fact 本体）\n"
                % (fields["failure_path"], fields["conditions"],
                   fields["ledger_ref"]) + CONFIRM_SECTION)
        path = os.path.join(pdir, "%s--pitfall-fact-%s.md" % (pid, _safe_name(fr["id"])))
        _atomic_write(path, _front(_order_fields(fields)) + "\n" + body)
        drafts.append({"file": os.path.relpath(path, out), "path": path,
                       "kind": "pitfall-fact", "id_preview": pid,
                       "title": fields["title"]})

    # ④K6 误报回流（功能11补件一）：重放证伪教训 → 哨兵规则草稿。
    # staging=distill 产物区 sentinel-staging/（knowledge 只读纪律不破）；
    # 草稿零进 drafts 列表——既有计数断言面零漂移，独立 sentinel_drafts 面。
    sen_rows = sentinel_rule_drafts(bat, date)
    if sen_rows:
        sdir = os.path.join(out, "sentinel-staging")
        os.makedirs(sdir, exist_ok=True)
        spath = os.path.join(sdir, "%s--sentinel-drafts.tsv" % _safe_name(name))
        _atomic_write(spath, _sentinel_draft_tsv(name, sen_rows))
        rep_sen = [{"file": os.path.relpath(spath, out), "rows": len(sen_rows)}]
    else:
        rep_sen = []

    # ⑤ 报告（确定性：无墙钟，日期锚自数据）
    rep = {
        "schema_version": 1, "generator": "distill-rules-v1", "battle": name,
        "gen": bat["gen"], "settled": bat["settled"], "recall": bat["recall"],
        "recall_hits": bat["recall_hits"], "recall_total": bat["recall_total"],
        "missing_total": len(bat["missing"]),
        "session": {"present": bool(bat["gen"]),
                    "findings_rows": len(bat["findings"]),
                    "timeline_rows": len(bat["timeline"]),
                    "facts_rows": len(bat["facts"])},
        "counts": {
            "technique_drafts": len([d for d in drafts if d["kind"] == "technique"]),
            "pitfall_drafts": len([d for d in drafts if d["kind"].startswith("pitfall")]),
            "pitfall_fp": len([d for d in drafts if d["kind"] == "pitfall-fp"]),
            "pitfall_miss": len([d for d in drafts if d["kind"] == "pitfall-miss"]),
            "pitfall_fact": len([d for d in drafts if d["kind"] == "pitfall-fact"]),
            "sentinel_drafts": len(sen_rows),
        },
        "drafts": drafts, "skipped": skipped,
        "sentinel_drafts": rep_sen,
    }
    # 落盘形去绝对路径（同输入异出目录两跑逐字节一致——确定性钉）；返回值保留
    # 绝对 path 供程序面直取。
    rep_json = dict(rep, drafts=[{k: v for k, v in d.items() if k != "path"}
                                 for d in drafts])
    _atomic_write(os.path.join(out, "distill-report.json"),
                  json.dumps(rep_json, ensure_ascii=False, indent=1,
                             sort_keys=True) + "\n")
    return rep


_STALE_DRAFT_RE = re.compile(r"^CP-\d{4}--(technique|pitfall)-.+\.md$")


def _clean_stale_drafts(kind_dir, kind):
    """重蒸馏=确定性重生成：清掉自家旧草案（只删本管线命名形的 .md，别的零碰）。"""
    try:
        names = os.listdir(kind_dir)
    except OSError:
        return
    for nm in names:
        if _STALE_DRAFT_RE.match(nm) and nm.count("--") == 1:
            try:
                os.unlink(os.path.join(kind_dir, nm))
            except OSError:
                pass


def _order_fields(fields):
    """避坑草案字段序=SCHEMA 九键先（gate.NEG_FIELD_ORDER 兼容），余键追加。"""
    order = [k for k in gate.NEG_FIELD_ORDER if str(fields.get(k, "")).strip()]
    for k in fields:
        if k not in order:
            order.append(k)
    return {k: fields[k] for k in order}


class _Counter(object):
    """草案编号预演计数器（CP-NNNN 连续推进；只读推演不锁号）。"""

    def __init__(self, start):
        m = re.match(r"^CP-(\d{4})$", start)
        self.n = int(m.group(1)) if m else 1

    def next(self):
        pid = "CP-%04d" % self.n
        self.n += 1
        return pid


# ======================================================== confirm（入册） ==

def read_negative_cards_for_test(knowledge_dir):
    """读面薄封装（gate.read_negative_cards 单源；测试/CLI 报账用）。"""
    return gate.read_negative_cards(knowledge_dir)


def confirm_draft(draft_path, knowledge_dir, reviewer):
    """人工确认后的草案 → write_negative_card(knowledge_dir, fields, body)。

    门：review_status 须为 accept（人工判读完成）；技法卡草案不走本面
    （正轨入册走 tanyin-knowledge commit 流——本舰只收负轨避坑卡）。
    编号=写面重分配（预演号不锁，防确认乱序撞号）。返回落卡路径。
    """
    import datetime
    text = _read_text(draft_path)
    fm = parse_front(text)
    if fm is None:
        raise RejectError("草案无 front matter: %s" % draft_path)
    if fm.get("kind") != "negative":
        raise RejectError("只收避坑卡草案（kind: negative）：本件 kind=%r——"
                          "技法卡草案走 tanyin-knowledge commit 流入册" % fm.get("kind"))
    if fm.get("review_status") != "accept":
        raise RejectError("草案未经人工确认（review_status=%r）——逐条勾完"
                          "「人工确认位」清单后改 accept 再来"
                          % fm.get("review_status"))
    if not str(reviewer or "").strip():
        raise DistillError("--reviewer 必填（谁确认的，入册留名）")
    fields = {k: v for k, v in fm.items()
              if k not in ("review_status", "id") and str(v).strip()}
    fields["judgment"] = _clip("人工确认 reviewer=%s" % reviewer, 200)
    today = datetime.date.today().isoformat()
    body = text.split("---", 2)[-1].lstrip("\n")
    body += ("\n## 人工确认\n- reviewer: %s\n- 确认日期: %s\n"
             "- 通道: cli.knowledge confirm → write_negative_card（锚接口）\n"
             % (reviewer, today))
    try:
        return gate.write_negative_card(knowledge_dir, fields, body)
    except gate.SeedFrozenError as e:
        raise DistillError(str(e))
    except ValueError as e:
        raise RejectError("避坑卡校验不过: %s" % e)


# ======================================================== suite 总报 ==

def suite_report(suite_dir):
    """逐战蒸馏报告聚合（<suite>/battle-*/distill/distill-report.json 扫读）。"""
    sd = os.path.abspath(suite_dir)
    if not os.path.isdir(sd):
        raise DistillError("套件目录不存在: %s" % sd)
    battles, skipped = [], []
    for name in sorted(os.listdir(sd)):
        if not _BATTLE_RE.match(name):
            continue
        rp = os.path.join(sd, name, "distill", "distill-report.json")
        if not os.path.isfile(rp):
            skipped.append({"battle": name,
                            "reason": "no-distill-report（未蒸馏或产物被清）"})
            continue
        try:
            rep = json.loads(_read_text(rp))
        except (ValueError, OSError) as e:
            skipped.append({"battle": name, "reason": "bad-json: %s" % e})
            continue
        battles.append({"battle": name, "gen": rep.get("gen"),
                        "settled": rep.get("settled"), "recall": rep.get("recall"),
                        "counts": rep.get("counts", {})})
    total_t = sum(b["counts"].get("technique_drafts", 0) for b in battles)
    total_fp = sum(b["counts"].get("pitfall_fp", 0) for b in battles)
    total_miss = sum(b["counts"].get("pitfall_miss", 0) for b in battles)
    total_fact = sum(b["counts"].get("pitfall_fact", 0) for b in battles)
    return {"schema_version": 1, "generator": "distill-rules-v1",
            "suite": sd,
            "counts": {"battles_seen": len(battles) + len(skipped),
                       "battles_distilled": len(battles),
                       "technique_drafts": total_t, "pitfall_drafts":
                       total_fp + total_miss + total_fact,
                       "pitfall_fp": total_fp, "pitfall_miss": total_miss,
                       "pitfall_fact": total_fact},
            "battles": battles, "skipped": skipped}
