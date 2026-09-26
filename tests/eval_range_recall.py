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
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cards as cards_mod  # noqa: E402
from ledger import core  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402

_DEFAULT_SESSION = os.path.join(HERE, "range", "session")   # 约定发现点（交战区分离：不入仓）


def _cell(t, row, col):
    return row[TABLES[t].index(col)]


def load_session(session_dir):
    """会话装载：(rows{表: 行集}, cards{EV id: 卡 dict})。坏卡跳过（容错面）。"""
    s = core.Session(session_dir)
    tables = ("findings.tsv", "assets.tsv", "creds.tsv", "intents.tsv",
              "E-index.tsv", "facts.tsv")
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


def score(rows, cards, gt):
    """召回裁决。返回 (recall=命中/len(gt), MISSING id 清单)。

    rows/cards 来自 load_session（纯函数面，可对夹具会话回归——不依赖 docker）。"""
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
    neg_targets = {_cell("facts.tsv", r, "target") for r in rows["facts.tsv"]
                   if _cell("facts.tsv", r, "kind") == "authz"}
    hits, missing = 0, []
    for e in gt:
        if e.get("polarity", "pos") == "neg":           # 负对（eval_authz_recall 兼容）
            ok = e.get("endpoint", "") in neg_targets
        else:
            ok = False
            for f in active:
                if not e.get("endpoint") or ast_value.get(
                        _cell("findings.tsv", f, "affected_asset_id")) != e["endpoint"]:
                    continue
                evs = [x for x in (_cell("findings.tsv", f, "evidence_ids") or "").split(";") if x]
                evs += [x for x in (_cell("findings.tsv", f, "control_evidence_ids") or "").split(";") if x]
                evs += linked.get(f[fi("id")], [])
                if e.get("marker", "") not in _word_markers(cards, evs):
                    continue
                if e.get("post_auth"):
                    ac = _cell("findings.tsv", f, "auth_context")
                    cred_ok = ac.startswith("CRED-") and cred_role.get(ac) == e.get("authz_role")
                    kind_ok = intent_kind.get(_cell("findings.tsv", f, "intent_id"),
                                              "").startswith("authz-diff")
                    if not (cred_ok or kind_ok):
                        continue                        # 认证后条目无 authz 链不计命中
                ok = True
                break
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
        gt = json.load(f)
    if isinstance(gt, dict):
        gt = gt.get("planted") or gt.get("entries") or []
    if not gt:
        sys.stderr.write("ground-truth 空\n")
        return 2
    rows, out_cards = load_session(session)
    recall, missing = score(rows, out_cards, gt)
    hit = len(gt) - len(missing)
    print("recall=%.2f (%d/%d)" % (recall, hit, len(gt)))
    for m in missing:
        print("MISSING\t" + m)
    return 0 if recall >= a.baseline else 1


if __name__ == "__main__":
    sys.exit(main())
