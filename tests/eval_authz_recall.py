# -*- coding: utf-8 -*-
"""批次4 T8：身份矩阵差分检出率 scorer（批次 6 接 LLM 在环复用；evals 可重放）。

用法：python3 tests/eval_authz_recall.py --goal-dir <D> --ground-truth <gt.json>
输出：recall=<hit>/<planted>＋MISSING\t<gt-id> 清单；exit 0=全检出（基线 1.0）否则 1。

匹配规则（计划 Produces 条款+负对扩展 Ruling）：
- 正对条目 {id,endpoint,role,marker}（polarity 缺省 pos）命中=存在 active finding 其
  auth_context 指向同 role 的 CRED，且 affected 资产值==endpoint，且该 finding 的证据
  EV 卡片（evidence_ids ∪ linked_finding 回链并集）expected.matchers 任一 word matcher
  的 words 列表含 marker。
- 负对条目（polarity=neg，回归基线）命中=存在 kind=authz 的 fact 其 target==endpoint。"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import cards, core  # noqa: E402
from ledger.schemas import TABLES  # noqa: E402


def _cell(t, row, col):
    return row[TABLES[t].index(col)]


def _word_markers(session, ev_ids):
    """EV 卡片 expected.matchers 中全部 word matcher 的 words 全集。"""
    out = set()
    for ev in ev_ids:
        row = next((r for r in session.rows("E-index.tsv") if r[0] == ev), None)
        if row is None:
            continue
        p = os.path.join(session.dir, _cell("E-index.tsv", row, "card_path"))
        if not os.path.isfile(p):
            continue
        try:
            card = cards.parse_ev_card(p)
        except cards.CardError:
            continue
        exp = card.get("expected")
        if not isinstance(exp, dict):
            continue
        for m in exp.get("matchers", []) or []:
            if isinstance(m, dict) and m.get("type") == "word":
                for w in m.get("words", []) or []:
                    out.add(str(w))
    return out


def hits(session, gt):
    cred_role = {r[0]: _cell("creds.tsv", r, "role") for r in session.rows("creds.tsv")}
    ast_value = {r[0]: _cell("assets.tsv", r, "value") for r in session.rows("assets.tsv")}
    latest_fd = {}
    for r in session.rows("findings.tsv"):
        latest_fd[r[0]] = r
    active = [r for r in latest_fd.values()
              if _cell("findings.tsv", r, "status") in ("", "active")]
    linked = {}
    for r in session.rows("E-index.tsv"):
        lf = _cell("E-index.tsv", r, "linked_finding")
        if lf:
            linked.setdefault(lf, []).append(r[0])
    neg_targets = {_cell("facts.tsv", r, "target") for r in session.rows("facts.tsv")
                   if _cell("facts.tsv", r, "kind") == "authz"}
    out = []
    for e in gt:
        if e.get("polarity", "pos") == "neg":
            ok = e.get("endpoint", "") in neg_targets
        else:
            ok = False
            for f in active:
                ac = _cell("findings.tsv", f, "auth_context")
                if not ac.startswith("CRED-") or cred_role.get(ac) != e.get("role"):
                    continue
                if e.get("endpoint") and ast_value.get(
                        _cell("findings.tsv", f, "affected_asset_id")) != e["endpoint"]:
                    continue
                evs = [x for x in (_cell("findings.tsv", f, "evidence_ids") or "").split(";") if x]
                evs += linked.get(f[0], [])
                if e.get("marker", "") in _word_markers(session, evs):
                    ok = True
                    break
        out.append((e, ok))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="身份矩阵差分检出率 scorer（基线 1.0）")
    ap.add_argument("--goal-dir", required=True)
    ap.add_argument("--ground-truth", required=True)
    a = ap.parse_args(argv)
    gt = json.load(open(a.ground_truth, encoding="utf-8"))
    if isinstance(gt, dict):
        gt = gt.get("planted") or gt.get("entries") or []
    if not gt:
        sys.stderr.write("ground-truth 空\n")
        return 2
    res = hits(core.Session(a.goal_dir), gt)
    hit = sum(1 for _e, ok in res if ok)
    print("recall=%d/%d" % (hit, len(gt)))
    missing = [e.get("id", "?") for e, ok in res if not ok]
    for m in missing:
        print("MISSING\t" + m)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
