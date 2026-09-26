# cli/ledger/evals_token_eff.py
# -*- coding: utf-8 -*-
"""G-11 token 校准通道：timeline usage 行实采→比值统计→校准报告+契约 v3 提案。

公式冻结不动（PROTOCOL §2）；本模块只产数据与提案，系数回写留契约 v3（裁决 G）。
usage 行形态=timeline.tsv event 列以 `usage:` 开头：
`usage: run=<run-id> tokens=<实际n> est_tokens=<估算m>`（契约 15 §6，T3 勘误）。"""
import json, os, statistics, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ledger.schemas import TABLES  # noqa: E402

_CMD_IDX = TABLES["timeline.tsv"].index("event")  # usage 行所在列（单源钉死；错位=测试断言红）


def extract_ratios(timeline_rows):
    """逐 usage 行取 tokens/est_tokens 比值。

    无 usage 行=EnvironmentError（CI 干跑无真跑数据=ENV-SKIP 非 FAIL）；
    usage 行形态残缺（缺 tokens/est_tokens 键）=ValueError fail-closed，不静默跳过。"""
    ratios = []
    for r in timeline_rows:
        c = r[_CMD_IDX] if len(r) > _CMD_IDX else ""
        if c.startswith("usage:"):
            kv = dict(p.split("=", 1) for p in c[len("usage:"):].split() if "=" in p)
            if "tokens" not in kv or "est_tokens" not in kv:
                raise ValueError("usage 行形态不符（契约 15 §6）：%s" % c)
            ratios.append(int(kv["tokens"]) / int(kv["est_tokens"]))
    if not ratios:
        raise EnvironmentError("无 usage 行（CI 干跑无真跑数据=ENV-SKIP 非 FAIL）")
    return ratios


def replay_verdict(states):
    """重放三态裁决：not-reproduced（未复现未处置）>0=FAIL。

    env-diff=已降级处置口径（P4 门；manual 同）；unhandled 计数入 actual 披露。"""
    counts = {}
    for s in states:
        counts[s] = counts.get(s, 0) + 1
    unhandled = counts.get("not-reproduced", 0)  # env-diff=已降级处置口径（P4 门）；manual 同
    counts["unhandled"] = unhandled
    return ("PASS" if unhandled == 0 else "FAIL"), counts


def write_calibration(ratios, out_path):
    """比值统计→校准报告落盘（n/median/min/max+契约 v3 系数候选提案+公式冻结注记）。"""
    rep = {"format_version": 1, "n": len(ratios),
           "median": statistics.median(ratios), "min": min(ratios), "max": max(ratios),
           "proposal": "契约 v3 系数候选：CJK/ASCII 混排实测中位比值 %.3f——回写 estimate_tokens 系数待 v3 微版本" % statistics.median(ratios),
           "frozen_note": "PROTOCOL §2 公式本批不改（裁决 G）"}
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    return rep
