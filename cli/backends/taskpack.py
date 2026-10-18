# -*- coding: utf-8 -*-
"""外部执行后端·任务包（功能24a §3 会话映射第一步）。

意图卡 → 任务包（goal+scope+预算+红线序列化）→ 后端会话。任务包=派给
外部肌肉的唯一公文：
- 最小披露律：外部后端拿到目标/范围/预算/红线/输出契约，拿不到账本全貌
  （不含凭据真值/auth 哈希/应急联系人——serialize 后可直发外部进程）。
- 预算分摊：goal.budget 三段（token;requests;hours，K/M/G 后缀=账本
  _seg_int 同语义）× intent.budget_share（无 share=全额）。
- 输出契约=归一入账（ingest.py）的对面：外部产出必须按账本枚举形状
  （findings C1/C2/C3/➖🙅 等），否则归一层拒收走原始流人工通道——
  枚举不发明第二套。

只读律：本模块对账本零写入（Session 只读面），写入全在 ingest.py 走
registry.lookup 既有执法链。
"""
import json
import re

from ledger.core import Session

PROTOCOL_VERSION = 1

_SEG = re.compile(r"^(\d+)([kKmMgG]?)$")
_MULT = {"": 1, "k": 1000, "m": 1000 ** 2, "g": 1000 ** 3}

#: 归一入账对面（与 ingest.py 同源枚举；账本 write_cmds 是唯一权威，
#: 这里是「对外告知」的镜像，枚举值不发明第二套）
OUTPUT_CONTRACT = {
    "facts": {
        "kind": ["port", "service", "http", "info", "vuln-clue", "authz"],
        "fields": ["kind", "target", "detail", "confidence"],
        "confidence": "[0,1] 浮点",
    },
    "findings": {
        "required": ["title", "confidence", "impact", "exploitation_status",
                     "scope_check", "description_brief", "reproducible_steps",
                     "affected_asset_id", "evidence"],
        "confidence": ["C1", "C2", "C3", "\u2796\U0001f6d1"],
        "impact": ["\u9ad8", "\u4e2d", "\u4f4e"],
        "exploitation_status": ["verified", "suspected", "ruled_out"],
        "scope_check": ["in_scope", "boundary-verified"],
        "evidence": {"fields": ["excerpt", "repro"], "note":
                     "每 finding 至少一条证据（铁律 4）——excerpt=观测原文，"
                     "repro=复现命令"},
    },
    " envelope": None,
}
OUTPUT_CONTRACT.pop(" envelope", None)


def _seg_int(s):
    m = _SEG.match(s or "")
    if not m:
        raise ValueError("预算段非法: %r" % (s,))
    return int(m.group(1)) * _MULT[m.group(2).lower()]


def parse_budget(raw):
    """goal.budget 三段 → (tokens, requests, hours)；缺段/坏段 fail-loud。"""
    parts = (raw or "").split(";")
    if len(parts) != 3:
        raise ValueError("预算须三段 token;requests;hours: %r" % (raw,))
    return tuple(_seg_int(p) for p in parts)


def _share_of(v, share):
    try:
        share_f = float(share)
    except (TypeError, ValueError):
        share_f = 1.0
    if not (0.0 < share_f <= 1.0):
        share_f = 1.0
    return int(v * share_f)


class TaskPackage(object):
    """任务包：build（账本只读组包）→ to_dict/serialize（直发外部）。"""

    def __init__(self, doc):
        self.doc = doc

    @staticmethod
    def build(goal_dir, intent_id, task_id):
        """从账本组包（只读）。意图不存在=fail-loud（派活引用闭合律）。"""
        s = Session(goal_dir)
        irows = [r for r in s.rows("intents.tsv") if r[0] == intent_id]
        if not irows:
            raise ValueError("intent 不存在: %s" % intent_id)
        intent = irows[-1]
        grows = s.rows("goals.tsv")
        if not grows:
            raise ValueError("goals.tsv 空——任务包无锚")
        goal = grows[-1]
        tokens, requests, hours = parse_budget(goal[11])
        share = intent[10]
        includes = [r for r in s.rows("scope.tsv") if r[1] == "include"]
        doc = {
            "v": PROTOCOL_VERSION,
            "task_id": task_id,
            "goal": {"id": goal[0], "target": goal[1], "objective": goal[2]},
            "scope": [{"matcher": r[2], "account": r[3],
                       "permitted_actions": r[4]} for r in includes],
            "budget": {"token_cap": _share_of(tokens, share),
                       "requests_cap": _share_of(requests, share),
                       "hours_cap": _share_of(hours, share),
                       "share": share or "1.0"},
            "redlines": {"rate_limit": goal[8], "window": goal[9],
                         "valid_until": goal[7], "guard_tier": goal[16],
                         "budget_hard": "超预算硬停——token_cap 触帽即停，"
                                        "不得续作"},
            "intent": {"id": intent[0], "title": intent[1],
                       "detail": intent[2], "engine": intent[4]},
            "output_contract": OUTPUT_CONTRACT,
        }
        return TaskPackage(doc)

    def to_dict(self):
        return self.doc

    def serialize(self):
        """确定性 JSON（sort_keys=可回放比对，直发外部进程 stdin）。"""
        return json.dumps(self.doc, ensure_ascii=False, sort_keys=True)
