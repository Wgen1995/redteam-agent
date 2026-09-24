# -*- coding: utf-8 -*-
"""EV/FD 卡片 front-matter 解析+TSV 同值性（契约 06；批4 T4）。

受限 YAML 子集复用 phases_engine.parse_yaml（块映射/列表/行内流/块标量全覆盖）。
双轨规则（§4.11）：标量 TSV 列为权威，卡片复核同值——不一致=P4 校验失败。"""


class CardError(Exception):
    pass


def parse_ev_card(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        raise CardError("卡片缺 front-matter 起始定界: " + path)
    parts = text.split("\n---\n", 1)
    if len(parts) != 2 or not parts[0][3:].strip():
        raise CardError("front-matter 未闭合或为空: " + path)
    from .phases_engine import parse_yaml, PhasesSyntaxError
    try:
        fields = parse_yaml(parts[0][3:])
    except PhasesSyntaxError as e:
        raise CardError("front-matter 语法错误: %s (%s)" % (e, path))
    if not isinstance(fields, dict) or "id" not in fields:
        raise CardError("front-matter 非 mapping 或缺 id: " + path)
    for k in ("network_position", "pair_group"):
        # parse_yaml 空值键=None（add-evidence 模板即产出 "pair_group: " 空行）：
        # 空值=未填，等同缺键放行（§4.11 TSV 权威，卡片复核只对非空同值执法）。
        if fields.get(k) is None:
            fields[k] = ""
        if k in fields and not isinstance(fields[k], str):
            raise CardError("%s 须为标量: %r" % (k, fields[k]))
    return fields


def check_consistency(card, eindex_row):
    from .schemas import TABLES
    cols = TABLES["E-index.tsv"]
    errs = []
    for card_key, col in (("id", "id"), ("title", "title"),
                          ("network_position", "network_position"),
                          ("pair_group", "pair_group")):
        cv = card.get(card_key, "")
        tv = eindex_row[cols.index(col)] if col in cols else ""
        if cv and tv and cv != tv:
            errs.append("%s 不同值: 卡片=%r TSV=%r" % (card_key, cv, tv))
    return errs
