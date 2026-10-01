BAND = (
    # 原表引用的 "SINK-SQLI"/"SINK-SSRF"/"SINK-AUTHZ"/"SINK-XSS" 在
    # knowledge/sinks/_index.md 里根本不存在（真实命名分别是 SINK-SQL-EXEC /
    # SINK-NET-REQUEST / SINK-AUTHZ-MISSING+SINK-OBJECT-AUTHZ / SINK-XSS-AUTOESCAPE+
    # SINK-XSS-RAWOUTPUT），导致 SQL 注入、越权、XSS 这三个 OWASP 高危类从未真正拿到
    # 高优先级，一直落进 _band() 的兜底最低优先级（len(BAND)）——Tomcat 实测撞见：
    # SQL-EXEC(69) 本该 band0，实际排在 band2 一堆噪音类之后。SSRF 的正确名字
    # SINK-NET-REQUEST 已经在 band1 里，不重复放进 band0。
    ("SINK-CODE-EXEC", "SINK-DESERIALIZE", "SINK-SQL-EXEC", "SINK-XXE", "SINK-AUTHZ-MISSING", "SINK-OBJECT-AUTHZ"),
    ("SINK-FILE-TRAVERSAL", "SINK-CMD-EXEC", "SINK-XSS-AUTOESCAPE", "SINK-XSS-RAWOUTPUT", "SINK-SSTI", "SINK-NET-REQUEST"),
)


HIGH_RISK_BANDS = frozenset({0, 1})


def _band(sink_type):
    st = sink_type or ""
    for i, names in enumerate(BAND):
        if st in names:
            return i
    return len(BAND)


def order_cards(cards):
    open_cards = [c for c in cards if c.get("status") in (None, "unchecked")]
    return sorted(open_cards, key=lambda c: (_band(c.get("sink_type")), c.get("sink_type") or "", c.get("module") or "", c.get("card_id") or ""))


def wake_blocked(cards, new_symbols):
    symbols = set(new_symbols or [])
    woken = []
    for card in cards:
        if card.get("status") != "blocked":
            continue
        deps = set(card.get("depends_on") or [])
        if deps & symbols:
            updated = dict(card)
            updated["status"] = "unchecked"
            woken.append(updated)
    return woken
