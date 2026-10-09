# -*- coding: utf-8 -*-
"""批次6 T16：授权靶场种 20 检出率 scorer（裁决 I；eval_authz_recall 匹配规则泛化复用）。

匹配规则（eval_authz_recall 泛化：role 匹配条件化+post_auth 链要求）：
- 命中=存在 active finding（status∈{"", "active"} 账本活集，eval_authz_recall 同口径）
  其 affected 资产值==gt.endpoint，且该 finding 证据集（evidence_ids ∪
  control_evidence_ids ∪ linked_finding 回链）EV 卡 expected.matchers 任一 word
  matcher 的 words 含 gt.marker；
- post_auth=true 条目另须 authz 链：intent kind=authz-diff（authz-diff 差分子流程）
  或 auth_context 指向 CRED 且该 CRED role==gt.authz_role（身份矩阵绑定）。
- 负对（polarity=neg）沿 eval_authz_recall：kind=authz fact target 命中（靶场 GT v1
  无负对，保留兼容）。

用法：python3 tests/eval_range_recall.py --session <D> --ground-truth tests/range/
ground-truth.json [--baseline 0.85]
退出码（裁决 I）：0=recall≥baseline；1=低于 baseline；2=环境（docker 缺且无
--session；或会话缺表——CI 无 docker 降级=2 ENV-skip，scorer 对夹具级金样 session
回归）。scorer 不代跑代理：无 --session 且 docker 在位=仍 2（干跑由 RUNBOOK 驱动，
R-T16-3）。
"""
import argparse
import json
import re
import os
import re
import shutil
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cards as cards_mod  # noqa: E402
from ledger import core  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

_DEFAULT_SESSION = os.path.join(HERE, "range", "session")   # 约定发现点（交战区分离：不入仓）


def _cell(t, row, col):
    return row[TABLES[t].index(col)]


def load_session(session_dir):
    """会话装载：(rows{表: 行集}, cards{EV id: 卡 dict})。坏卡跳过（容错面）。
    批次 9 三轮战精度门：timeline 一并入载——重放三态与 replay-probe 裁决为
    命中前置（无 VERIFIED 在案的证据不计数=幻觉/未验面零分；最新探针裁决
    not-reproduced 未翻案的证据同样不计——G-52 越权改判防线在评分侧复设）。"""
    s = core.Session(session_dir)
    tables = ("findings.tsv", "assets.tsv", "creds.tsv", "intents.tsv",
              "E-index.tsv", "facts.tsv", "timeline.tsv")
    rows = {t: s.rows(t) for t in tables}
    out_cards = {}
    ci = TABLES["E-index.tsv"].index("card_path")
    for r in rows["E-index.tsv"]:
        p = os.path.join(session_dir, r[ci])
        if not os.path.isfile(p):
            continue
        try:
            out_cards[r[0]] = cards_mod.parse_ev_card(p)
        except cards_mod.CardError:
            continue
    return rows, out_cards


def _word_markers(cards, ev_ids):
    out = set()
    for ev in ev_ids:
        exp = (cards.get(ev) or {}).get("expected")
        if not isinstance(exp, dict):
            continue
        for m in exp.get("matchers", []) or []:
            if isinstance(m, dict) and m.get("type") == "word":
                out |= {str(w) for w in m.get("words", []) or []}
    return out


_URL_RE = re.compile(r"https?://[0-9A-Za-z_.:\-]+(?:/[0-9A-Za-z_./%\-\{\}?=&]*)?")


def _ev_endpoint_keys(evs, cards, eindex_rows, aliases):
    """v7 键控（battle-25 裸战士实证）：EV 报文首行+Host 头、E-index 描述 URL——
    端点键提取面。服务级资产记账的 findings 由本面补路径（行为在案即入键）。"""
    out = set()
    desc = {r[0]: (r[5] if len(r) > 5 else "") for r in eindex_rows}

    def _safe_canon(u):
        try:
            return _canon_endpoint(u, aliases)
        except ValueError:
            return None          # 畸形 URL 文本不入键（描述自由文本容错）

    for ev in evs:
        rr = str((cards.get(ev) or {}).get("raw_request") or "")
        lines = rr.splitlines()
        if lines and " HTTP/" in lines[0]:
            parts = lines[0].split()
            if len(parts) >= 2 and parts[1].startswith("/"):
                host = ""
                for ln in lines[1:]:
                    if ln.lower().startswith("host:"):
                        host = ln.split(":", 1)[1].strip()
                        break
                if host:
                    k = _safe_canon(host + parts[1])
                    if k:
                        out.add(k)
        for m in _URL_RE.finditer(str(desc.get(ev, ""))):
            k = _safe_canon(m.group(0))
            if k:
                out.add(k)
    return out
    return out


def _norm_endpoint(u):
    """URL 归一（批次 7 T16 首战键失配①）：小写 host/剥默认端口/query 排序/去尾斜杠。
    只归语法不归语义——语义别名一律走 GT host_aliases 显式声明（禁猜测式映射）。"""
    s = urlsplit(u if "://" in u else "//" + u)
    host = (s.hostname or "").lower()
    net = host if s.port in (None, 80, 443) else "%s:%d" % (host, s.port)
    path = s.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    q = urlencode(sorted(parse_qsl(s.query)))
    return net + path + (("?" + q) if q else "")


def _canon_host(netloc, aliases):
    """语义别名统一（批次 7 T16）：netloc 命中 canonical 自身或其 host_aliases 清单⇒归一。
    未声明的值原样返回——只认显式声明，禁猜测式映射。"""
    for canon, al in (aliases or {}).items():
        if netloc == canon or netloc in al:
            return canon
    return netloc


def _canon_endpoint(u, aliases):
    """全键归一 v4（battle-5 P2#6，dict §四勘误）：host 段走 _canon_host 语义统一；
    **query 整体剥离**——GT 键的参数名/值/编码是布靶者书写形，诚实黑盒战士的探测
    参数不可预知且种子按路径前缀匹配行为 ⇒ 检出键=host+path。battle-2 作者读 GT
    对齐键形掩盖了该缺陷，独立战士（三轮）以 14 枚行为命中被键形误罚暴露之。
    v4 新律（尾段数字归一）：路径尾段纯数字 → {n}——idor 资源 id 同值差
    （/invoice/2 vs /invoice/88）不再卡分；非数字尾段（.env 等）原样。
    query 保留于 GT 文档面（复现提示），不参与匹配。"""
    k = _norm_endpoint(u)
    i = k.find("/")
    host = k if i < 0 else k[:i]
    rest = "" if i < 0 else k[i:]
    qi = rest.find("?")
    if qi >= 0:                                   # v3：query 剥离（探测形不入键）
        rest = rest[:qi]
    segs = rest.rsplit("/", 1)                   # v4：尾段纯数字归一 {n}
    if len(segs) == 2 and segs[1] and segs[1].isdigit():
        rest = segs[0] + "/{n}"
    return _canon_host(host, aliases) + rest


KEYING_VERSION = 7   # v7 服务级资产回退（battle-25 裸战士：findings 挂服务级资产时端点键取 EV 报文/描述 URL——docker 网 IP 别名显式入 GT host_aliases）+v6 FD 键别名 +v5 alt-form 孪生键+v4.1 两遍法


def _replay_state(rows):
    """重放三态推导（批次 9 三轮战精度门/G-52）：timeline 事件溯源末值。
    verified=最新 replay:<id>:<state> 为 VERIFIED/REPAIRED 的 id 集；
    blocked=最新 replay-probe 裁决 not-reproduced 且无更晚 reproduced 的 id 集
    （越权 VERIFIED 改判在 CLI 缝⑪已拒，此处评分侧复设防线——纵深）。"""
    latest_state, probe_last = {}, {}
    for r in rows.get("timeline.tsv", []):
        ev = _cell("timeline.tsv", r, "event")
        m = re.match(r"replay:(\S+?):(VERIFIED|REPAIRED|REJECTED)", ev)
        if m:
            latest_state[m.group(1)] = m.group(2)
        m2 = re.search(r"replay-probe (\S+) verdict=(\S+)", ev)
        if m2:
            probe_last[m2.group(1)] = m2.group(2)
    verified = {i for i, st in latest_state.items() if st in ("VERIFIED", "REPAIRED")}
    blocked = {i for i, v in probe_last.items() if v == "not-reproduced"}
    return verified, blocked


def score(rows, cards, gt, host_aliases=None, tracks=None):
    """召回裁决。返回 (recall=命中/len(gt), MISSING id 清单)。

    rows/cards 来自 load_session（纯函数面，可对夹具会话回归——不依赖 docker）。
    批次 7 T16：gt 兼容条目清单或 GT 文档 dict（顶层 host_aliases 别名声明，None 容错；
    既有 3 参调用形不变）；endpoint 匹配两侧先 _norm_endpoint 语法归一再 _canon_host
    语义别名统一——只归语法不归语义，语义等价必须显式进 host_aliases。
    battle-5 T2（P2#1）双轨：beacon 轨（marker 词证）+差分轨（authz_diff 非空或
    EV pair_group 控制对；无 marker 亦可计——检出主通道从「答案回显」转向行为差分）。
    tracks 字典可选回填 {'beacon': n, 'diff': n}（recall=并集）。"""
    if isinstance(gt, dict):
        aliases = gt.get("host_aliases") or host_aliases or {}
        gt = gt.get("planted") or gt.get("entries") or gt.get("items") or []
    else:
        aliases = host_aliases or {}
    fi = TABLES["findings.tsv"].index
    latest = {}
    for r in rows["findings.tsv"]:
        latest[r[fi("id")]] = r
    active = [r for r in latest.values() if r[fi("status")] in ("", "active")]
    ast_value = {r[0]: _cell("assets.tsv", r, "value") for r in rows["assets.tsv"]}
    cred_role = {r[0]: _cell("creds.tsv", r, "role") for r in rows["creds.tsv"]}
    intent_kind = {}
    for r in rows["intents.tsv"]:                       # 事件溯源末值
        intent_kind[r[0]] = _cell("intents.tsv", r, "kind")
    linked = {}
    for r in rows["E-index.tsv"]:
        lf = _cell("E-index.tsv", r, "linked_finding")
        if lf:
            linked.setdefault(lf, []).append(r[0])
    verified_ev, blocked_ev = _replay_state(rows)   # 精度门：重放实证前置
    # v6 FD 键别名（battle-13 G-r14 实证）：timeline 重放行可键 FD（replay:FD-x:VERIFIED）
    # ——语义等价（该 finding 全部 EV 已重放）；按 findings 证据链展开为 EV 键。
    # REJECTED 的 FD 同步阻断其全部 EV（诚实降级语义随链传播）。EV 键行不受影响。
    _fd_evs = {}
    for r in rows.get("findings.tsv", []):
        _evs = [x for x in (_cell("findings.tsv", r, "evidence_ids") or "").split(";") if x]
        _evs += [x for x in (_cell("findings.tsv", r, "control_evidence_ids") or "").split(";") if x]
        _fd_evs[r[fi("id")]] = _evs
    for _fd in [i for i in list(verified_ev) if i.startswith("FD-")]:
        verified_ev |= set(_fd_evs.get(_fd, ()))
    for _fd in [i for i in list(blocked_ev) if i.startswith("FD-")]:
        blocked_ev |= set(_fd_evs.get(_fd, ()))
    neg_targets = {_cell("facts.tsv", r, "target") for r in rows["facts.tsv"]
                   if _cell("facts.tsv", r, "kind") == "authz"}
    hits, missing = 0, []
    consumed = set()   # v4 反膨胀律：一枚 finding 至多满足一枚 GT（同键多 GT 须各自实证）
    if tracks is not None:
        tracks.setdefault("beacon", 0)
        tracks.setdefault("diff", 0)

    def _match(e, pass_mode):
        """单 GT 对 active findings 配型。pass 1（'beacon'）只认词证；pass 2（'diff'）
        只认差分。v4.1 两遍法：词证永远优先于差分——G-r7 实证一遍法按 GT 序会让
        先序 GT 的差分耗用后序 GT 的词证 finding（证据强度倒挂）；两遍保总分不变、
        归因归真（词证侧 GT 先得）。返回 (finding_id, track) 或 (None, None)。"""
        gt_keys = {_canon_endpoint(e["endpoint"], aliases)} if e.get("endpoint") else set()
        for alt in e.get("alt_forms", ()):        # v5 孪生键：语义等价必须显式（GT 条目级声明）
            gt_keys.add(_canon_endpoint(alt, aliases))
        for f in active:
            f_id = f[fi("id")]
            if f_id in consumed:               # v4：已被前序 GT 消费的 finding 不得再计
                continue
            av = ast_value.get(_cell("findings.tsv", f, "affected_asset_id"))
            evs = [x for x in (_cell("findings.tsv", f, "evidence_ids") or "").split(";") if x]
            evs += [x for x in (_cell("findings.tsv", f, "control_evidence_ids") or "").split(";") if x]
            evs += linked.get(f[fi("id")], [])
            if not gt_keys or av is None:
                continue
            if _canon_endpoint(av, aliases) not in gt_keys:
                # v7 服务级资产回退：路径取自 EV 报文/描述（端点级资产直配优先不变）
                if not _ev_endpoint_keys(evs, cards, rows.get("E-index.tsv", []), aliases) & gt_keys:
                    continue
            if not any(x in verified_ev for x in evs):
                continue        # 精度门：无重放 VERIFIED 在案的证据不计（幻觉面零分）
            if any(x in blocked_ev for x in evs):
                continue        # 精度门：未翻案 not-reproduced 证据拖累整 finding
            beacon_hit = (e.get('marker') or '') in _word_markers(cards, evs)
            if pass_mode == "beacon":
                if not beacon_hit:
                    continue
            else:                            # T2 差分轨：无词证时按差分源实证
                if beacon_hit:
                    continue                 # 词证可计的 finding 留给词证遍
                diff_hit = bool(_cell("findings.tsv", f, "control_evidence_ids"))
                if not diff_hit:
                    ei = TABLES["E-index.tsv"].index("pair_group")
                    diff_hit = any(len(r) > ei and r[ei]
                                   for r in rows.get("E-index.tsv", [])[1:]
                                   if r[0] in evs)
                if not diff_hit:
                    continue
            if e.get("post_auth"):
                ac = _cell("findings.tsv", f, "auth_context")
                cred_ok = ac.startswith("CRED-") and cred_role.get(ac) == e.get("authz_role")
                kind_ok = intent_kind.get(_cell("findings.tsv", f, "intent_id"),
                                          "").startswith("authz-diff")
                if not (cred_ok or kind_ok):
                    continue                    # 认证后条目无 authz 链不计命中
            return f_id, ("beacon" if beacon_hit else "diff")
        return None, None

    results = {}   # v4.1：gt-id -> track（先词证遍后差分遍，两遍合一裁决）
    for pass_mode in ("beacon", "diff"):
        for e in gt:
            if e.get("id") in results or e.get("polarity", "pos") == "neg":
                continue
            f_id, track = _match(e, pass_mode)
            if f_id:
                results[e.get("id")] = track
                consumed.add(f_id)             # v4：单计登记
    for e in gt:
        if e.get("polarity", "pos") == "neg":           # 负对（eval_authz_recall 兼容）
            ok = e.get("endpoint", "") in neg_targets
        elif e.get("id") in results:
            ok = True
            if tracks is not None:                  # T2 双轨分列（v4.1 词证优先）
                tracks[results[e.get("id")]] = tracks.get(results[e.get("id")], 0) + 1
        else:
            ok = False
        if ok:
            hits += 1
        else:
            missing.append(e.get("id", "?"))
    recall = (hits / len(gt)) if gt else 0.0
    return recall, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description="授权靶场种 20 检出率 scorer（裁决 I）")
    ap.add_argument("--session", default=None, help="现成会话目录（干跑产物；缺省走约定发现点/docker 探测）")
    ap.add_argument("--ground-truth", required=True)
    ap.add_argument("--baseline", type=float, default=0.85)
    a = ap.parse_args(argv)
    session = a.session
    if session is None:
        session = os.environ.get("TANYIN_RANGE_SESSION") or _DEFAULT_SESSION
        if not os.path.isfile(os.path.join(session, "findings.tsv")):
            if shutil.which("docker") is None:
                sys.stderr.write("docker 缺且无现成靶场会话——ENV 降级 exit 2（裁决 I；"
                                 "scorer 对夹具级金样 session 回归）\n")
            else:
                sys.stderr.write("无现成靶场会话（%s）——scorer 不代跑代理，干跑由 "
                                 "RUNBOOK 驱动后以 --session 指定（exit 2）\n" % session)
            return 2
    if not os.path.isfile(os.path.join(session, "findings.tsv")):
        sys.stderr.write("会话目录无效（缺 findings.tsv）: %s\n" % session)
        return 2
    with open(a.ground_truth, encoding="utf-8") as f:
        doc = json.load(f)
    entries = doc if isinstance(doc, list) else (
        doc.get("planted") or doc.get("entries") or [])
    if not entries:
        sys.stderr.write("ground-truth 空\n")
        return 2
    rows, out_cards = load_session(session)
    tracks = {}
    recall, missing = score(rows, out_cards, doc if isinstance(doc, dict) else entries,
                            tracks=tracks)
    hit = len(entries) - len(missing)
    print("recall=%.2f (%d/%d)" % (recall, hit, len(entries)))
    print("track_beacon=%d track_diff=%d (双轨分列：词证/差分实证；keying v%d)"
          % (tracks.get("beacon", 0), tracks.get("diff", 0), KEYING_VERSION))
    for m in missing:
        print("MISSING\t" + m)
    return 0 if recall >= a.baseline else 1


if __name__ == "__main__":
    sys.exit(main())
