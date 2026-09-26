# -*- coding: utf-8 -*-
"""五宿主矩阵单源（批次 6 T8）——宿主模板直读+AGENTS 系统级注入渲染/幂等注入。

- host_compat(repo_root, host)：install/hosts/<host>.json 直读（verification/compat/
  egress_default_tier 发布口径字段；walcode/CodeBuddy=静态验证+待实测 §10.3→G-38）。
- render_agents_inject(repo_root, host)：install/AGENTS-INJECT.md 常驻八条模板+本宿主
  档位披露行 → <!--TANYIN:BEGIN/END--> 标记包裹块（<2K token 量级护栏 ≈4 char/token）。
- inject_agents(agents_path, block)：标记包裹幂等替换——已注入=原位换块；未注入=文末追加。
机械投影/模板渲染面（铁律 7）：只渲染不造数据；档位披露行照模板字段直译（铁律 5 如实披露）。
写面 LF 字节纪律（newline 显式）。"""
import json
import os

MARK_BEGIN = "<!--TANYIN:BEGIN-->"
MARK_END = "<!--TANYIN:END-->"
_INJECT_MD = os.path.join("install", "AGENTS-INJECT.md")
_NL = chr(10)   # LF 字面量（避免转义形参漂移）


def _tpl_path(repo_root, host):
    return os.path.join(repo_root, "install", "hosts", host + ".json")


def host_compat(repo_root, host):
    """宿主装载模板直读（dict）；模板缺=FileNotFoundError（fail-closed 不猜）。"""
    with open(_tpl_path(repo_root, host), encoding="utf-8") as f:
        d = json.load(f)
    if d.get("host") != host:
        raise ValueError("宿主模板 host 字段不符: %s vs %s" % (d.get("host"), host))
    return d


def _tier_disclosure(tpl):
    tier = tpl.get("egress_default_tier", 1)
    if "待实测" in tpl.get("verification", ""):
        return "Tier %d（宿主待实测——G-38 实测回传后升档；保守披露）" % tier
    return "Tier %d" % tier


def render_agents_inject(repo_root, host):
    """AGENTS 系统级注入块：常驻八条+本宿主档位披露行（标记包裹，供幂等注入消费）。"""
    tpl = host_compat(repo_root, host)
    with open(os.path.join(repo_root, _INJECT_MD), encoding="utf-8") as f:
        body = f.read().rstrip(_NL)
    body = body.replace("{{HOST}}", host).replace(
        "{{TIER_DISCLOSURE}}", _tier_disclosure(tpl))
    return MARK_BEGIN + _NL + body + _NL + MARK_END


def inject_agents(agents_path, block):
    """标记包裹幂等替换：已有注入=原位换新块（首尾标记外内容零触碰）；
    未注入=文末空行后追加。LF 字节纪律（newline 显式）。"""
    with open(agents_path, encoding="utf-8") as f:
        text = f.read()
    head, sep, tail = text.partition(MARK_BEGIN)
    if sep:
        _, _, after = tail.partition(MARK_END)
        new = head + block + after
    else:
        new = text.rstrip(_NL) + _NL + _NL + block + _NL
    with open(agents_path, "w", encoding="utf-8", newline=_NL) as f:
        f.write(new)
