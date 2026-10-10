# -*- coding: utf-8 -*-
"""CVSS v3.1 base 计算器（v0.5b G2，渗透专家项）——纯函数零依赖。

base(av,ac,pr,ui,s,c,i,a)：AttackVector/Complexity/PrivRequired/UserInteraction/
Scope/Confidentiality/Integrity/Availability → 0.0-10.0（Roundup 按规范）。
severity：<4 low；<7 medium；<9 high；>=9 critical；0 none。"""
_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC = {"L": 0.77, "H": 0.44}
_PR_U = {"N": 0.85, "L": 0.62, "H": 0.27}     # Scope=Unchanged 权重（PR 枚举 N/L/H）
_PR_C = {"N": 0.85, "L": 0.68, "H": 0.5}      # Scope=Changed 权重
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"H": 0.56, "L": 0.22, "N": 0.0}


def _fail(msg):
    raise ValueError("CVSS 指标非法: " + msg)


def base(av, ac, pr, ui, s, c, i, a):
    """v3.1 base score（官方公式）；非法枚举值=ValueError。"""
    av, ac, pr, ui, s = av.upper(), ac.upper(), pr.upper(), ui.upper(), s.upper()
    c, i, a = c.upper(), i.upper(), a.upper()
    if av not in _AV:
        _fail("AV=" + av)
    if ac not in _AC:
        _fail("AC=" + ac)
    if ui not in _UI:
        _fail("UI=" + ui)
    if s not in ("U", "C"):
        _fail("S=" + s)
    pr_map = _PR_C if s == "C" else _PR_U
    if pr not in pr_map:
        _fail("PR=" + pr)
    for name, v in (("C", c), ("I", i), ("A", a)):
        if v not in _CIA:
            _fail(name + "=" + v)
    iss = 1.0 - (1.0 - _CIA[c]) * (1.0 - _CIA[i]) * (1.0 - _CIA[a])
    if s == "U":
        impact = 6.42 * iss
    else:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    if impact <= 0:
        return 0.0
    exploitability = 8.22 * _AV[av] * _AC[ac] * pr_map[pr] * _UI[ui]
    if s == "U":
        score = min(impact + exploitability, 10.0)
    else:
        score = min(1.08 * (impact + exploitability), 10.0)
    # Roundup（规范）：小数点后一位向上进
    import math
    return round(math.ceil(score * 10) / 10.0, 1)


def severity(score):
    """严重度分档：none/low/medium/high/critical（规范阈值）。"""
    if score <= 0:
        return "none"
    if score < 4.0:
        return "low"
    if score < 7.0:
        return "medium"
    if score < 9.0:
        return "high"
    return "critical"
