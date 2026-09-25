# -*- coding: utf-8 -*-
"""G-33 双锚互证：交战区 approvals.tsv(knowledge-approved) ↔ 库侧 log.md approve 行。

配对键=(page_id, approver, timestamp 精确到秒)。approvals note 列按 note_pattern 抽页面 id
（approve --knowledge 落账形态核对为先：实跑一次抓 note 字节，若形态变化改 pattern 不改本函数）。
任一侧缺配对=指标 FAIL（硬门，裁决 E）；孤儿行（单侧在）由 missing 清单列明细。"""
import re


def _ledger_side(rows, pat):
    out = {}
    for r in rows:  # 列序 [id,command_hash,decision,approver,timestamp,note,schema_version]
        if len(r) > 5 and r[2] == "knowledge-approved":
            m = re.search(pat, r[5] or "")
            if m:
                out[(m.group(1), r[3] or "", r[4] or "")] = r[0]
    return out


def _knowledge_side(log_text):
    out = {}
    for ln in log_text.splitlines():
        cols = ln.split("|")
        if len(cols) >= 4 and cols[1] == "approve":
            ap = ""
            for c in cols[3:]:
                if c.startswith("approver="):
                    ap = c[len("approver="):].split("（")[0]
            out[(cols[2], ap, cols[0])] = ln
    return out


def check(approvals_rows, log_text, note_pattern=r"\b([A-Z]{2,3}-\d{4})\b"):
    # R-T2-5：默认 pattern 由计划示意 ([A-Z]{2}-\d{4}) 调整——在库页 id 前缀实测 2-3 字母
    # （STG/CP/PR/KP；STG-0001 会被 2 字母形误抽为 TG-0001），加词界防子串误抽；
    # 计划自注「实跑抓 note 字节后可改 pattern 不改本函数」即此通道。
    # R-T2-6：matched 三元组序按裁决 E 原文 (page-id, timestamp, approver)——计划代码
    # 示意键序 (page-id, approver, timestamp) 与自身测试断言冲突，以裁决 E 为准。
    led, kn = _ledger_side(approvals_rows, note_pattern), _knowledge_side(log_text)
    matched = sorted((k[0], k[2], k[1]) for k in led.keys() & kn.keys())
    return {"matched": matched,
            "missing_in_knowledge": sorted(k[0] for k in led.keys() - kn.keys()),
            "missing_in_ledger": sorted(k[0] for k in kn.keys() - led.keys())}
