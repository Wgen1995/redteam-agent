# -*- coding: utf-8 -*-
"""matcher 子集评估器（R1/G-17；契约 06 微版本勘误）。

子集：word（words[]+condition or|and，默认 and）/ status（status[]）/ regex extractor；
多 matcher 语义=全部命中（AND）；未知 type raise MatcherError（fail-closed）。"""


class MatcherError(Exception):
    pass


def _word(m, body):
    words = m.get("words")
    if not isinstance(words, list) or not words:
        raise MatcherError("word matcher 缺 words[]: %r" % m)
    cond = m.get("condition", "and")
    if cond not in ("and", "or"):
        raise MatcherError("word condition 仅 and|or: %r" % cond)
    if cond == "or":
        return any(w in body for w in words)
    return all(w in body for w in words)


def _status(m, status):
    st = m.get("status")
    if not isinstance(st, list) or not st:
        raise MatcherError("status matcher 缺 status[]: %r" % m)
    return status in [int(x) for x in st]


def evaluate(expected, status, headers, body):
    """expected={}→matched=None（manual：无 matcher 无法机械判定）。"""
    if not expected or not expected.get("matchers"):
        return {"matched": None, "results": [], "extracted": {}}
    results, ok_all, extracted = [], True, {}
    for m in expected.get("matchers", []):
        t = m.get("type")
        if t == "word":
            ok = _word(m, body)
            results.append({"type": "word", "detail": m.get("words"), "ok": ok})
        elif t == "status":
            ok = _status(m, status)
            results.append({"type": "status", "detail": m.get("status"), "ok": ok})
        else:
            raise MatcherError("matcher type 不在子集 {word,status}: %r" % t)
        ok_all = ok_all and ok
    for e in expected.get("extractors", []):
        if e.get("type") != "regex":
            raise MatcherError("extractor type 不在子集 {regex}: %r" % e.get("type"))
        import re
        pats = e.get("regex") or []
        if not isinstance(pats, list) or not pats:
            raise MatcherError("regex extractor 缺 regex[]: %r" % e)
        mo = re.search(pats[0], body)
        if mo:
            extracted[e.get("name", "")] = mo.group(1) if mo.groups() else mo.group(0)
    return {"matched": ok_all, "results": results, "extracted": extracted}
