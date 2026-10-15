# -*- coding: utf-8 -*-
"""OP2 UA 治理单源（docs/reviews/2026-10-10-nine-expert-review/02-opsec.md 缺口#1
「UA 自报家门——一条 IDS 规则全量归因」+ 建议表「禁自名 UA+replay --ua」；
计划 docs/superpowers/plans/2026-10-14-opsec-wallclock.md Task OP2）。

- NEUTRAL_UA：中性默认（常见兼容形，零平台指纹）；
- SELF_UA_RE：自名形态——tanyin/probe/replay/drill 家族（含 wN-probe、
  G-rN-drill 等夹具探针变体全录）；第三方 UA（Mozilla/curl/Wget/
  Go-http-client…）不匹配（保真透传，重放保真不归因）；
- resolve_ua()：--ua 显式覆盖 > 卡片第三方 UA 保真（返回 None=保持原值）>
  env TANYIN_UA 可配默认 > NEUTRAL_UA。

单源消费者：cli/tanyin-replay（出站最后一道整形）与 tests/test_op2_ua.py
（仓内自名点位清零扫描——判别式禁分叉）。
"""
import re

NEUTRAL_UA = "Mozilla/5.0 (compatible)"
ENV_UA = "TANYIN_UA"
SELF_UA_RE = re.compile(
    r"(?i)\A(tanyin[-\w./]*|probe[\d./+-]*|w\d+[-_]?probe[-\w./]*|replay/\d[\w.]*|"
    r"[\w.-]*-(probe|drill)[\w./-]*|g-r\d+[-\w./]*)\Z")


def is_self_named(ua):
    """UA 值是否自报家门（tanyin/probe/replay/drill 家族）。"""
    return bool(ua) and bool(SELF_UA_RE.match(ua.strip()))


def resolve_ua(card_ua, flag_ua, env_ua):
    """重放出站 UA 裁决：--ua 显式 > 第三方卡值保真(None) > env/中性默认。

    flag_ua/--ua 与 env_ua(TANYIN_UA) 为空串视同未提供。
    """
    if flag_ua:
        return flag_ua
    if card_ua and not is_self_named(card_ua):
        return None
    return env_ua or NEUTRAL_UA
