# -*- coding: utf-8 -*-
"""tanyin-phases 引擎库（批次 3）——phases.yaml 确定性状态机运算（铁律 7 允许类 1）。
子命令实现按任务渐进落位（T2 validate / T3 gate / T6 restart / T7 resume-kit / T8 cached /
T5 rebuild-state）；dispatch 在 T2 随入口一并接通。
契约：contracts/04（yaml schema）+ phases/PROTOCOL.md（断言→命令调用协议/常驻集清单）。"""
import io, os, re, shlex, sys
from contextlib import redirect_stdout, redirect_stderr

from . import core
from .core import GATE_ORDER

DEFAULT_YAML = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "phases", "phases.yaml")


class PhasesSyntaxError(ValueError):
    """受限 YAML 子集语法外输入（fail-closed，不猜）。"""


def _strip_comment(line):
    out, q = [], None
    for i, ch in enumerate(line):
        if q:
            out.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch; out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _split_flow(body):
    parts, depth, q, cur = [], 0, None, []
    for ch in body:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch; cur.append(ch)
        elif ch in "[{":
            depth += 1; cur.append(ch)
        elif ch in "]}":
            depth -= 1; cur.append(ch)
            if depth < 0:
                raise PhasesSyntaxError("流集合闭括号多余: %r" % body)
        elif ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if q is not None:
        raise PhasesSyntaxError("流集合引号未闭合: %r" % body)
    if depth != 0:
        raise PhasesSyntaxError("流集合括号未闭合: %r" % body)
    if cur:
        parts.append("".join(cur))
    return [p for p in (x.strip() for x in parts) if p]


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_flow(tok):
    tok = tok.strip()
    if tok[:1] in "{[":
        closer = "}" if tok[0] == "{" else "]"
        if len(tok) < 2 or not tok.endswith(closer):
            raise PhasesSyntaxError("流集合未闭合: %r" % tok)
        body = tok[1:-1].strip()
        if tok[0] == "{":
            if not body:
                return {}
            m = {}
            for part in _split_flow(body):
                k, _, v = part.partition(":")
                m[_unquote(k)] = _parse_flow(v)
            return m
        return [] if not body else [_parse_flow(p) for p in _split_flow(body)]
    if tok[-1:] in "}]":
        raise PhasesSyntaxError("流集合开括号缺失: %r" % tok)
    return _unquote(tok)


def parse_yaml(text):
    """受限子集：块映射/块列表/行内流映射/行内流列表/引号与裸标量/#注释/>- 与 | 块标量。"""
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw)
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip(" "))
        if "\t" in s[:indent + 1]:
            raise PhasesSyntaxError("缩进禁 tab: %r" % raw)
        lines.append((indent, s.strip()))
    pos = [0]

    def parse_node(indent):
        if pos[0] >= len(lines) or lines[pos[0]][0] < indent:
            return None
        if lines[pos[0]][1] == "-" or lines[pos[0]][1].startswith("- "):
            return parse_seq(lines[pos[0]][0])
        return parse_map(lines[pos[0]][0])

    def parse_seq(indent):
        out = []
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or not (con == "-" or con.startswith("- ")):
                break
            item = con[1:].strip()
            pos[0] += 1
            if not item:
                out.append(parse_node(indent + 2))
            elif ":" in item and not item.startswith(("{", "[", "\"", "'")):
                out.append(_map_from(indent, item))
            else:
                out.append(_parse_flow(item))
        return out

    def _map_from(indent, first):
        m = {}
        k, _, v = first.partition(":")
        m[_unquote(k)] = _val(indent, v)
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or con.startswith("- "):
                break
            k, _, v = con.partition(":")
            pos[0] += 1
            m[_unquote(k)] = _val(indent, v)
        return m

    def _val(indent, v):
        v = v.strip()
        if not v:
            return parse_node(indent + 2)
        return _parse_flow(v)

    def parse_map(indent):
        m = {}
        while pos[0] < len(lines):
            ind, con = lines[pos[0]]
            if ind != indent or con.startswith("- "):
                break
            if ":" not in con:
                raise PhasesSyntaxError("映射行缺冒号: %r" % con)
            k, _, v = con.partition(":")
            pos[0] += 1
            v = v.strip()
            if v in (">", ">-", "|", "|-"):
                m[_unquote(k)] = _fold(indent, v)
            elif v:
                m[_unquote(k)] = _parse_flow(v)
            else:
                m[_unquote(k)] = parse_node(indent + 2)
        return m

    def _fold(indent, style):
        parts, base = [], None
        while pos[0] < len(lines) and lines[pos[0]][0] > indent:
            ind, con = lines[pos[0]]
            base = ind if base is None else base
            if ind < base:
                break
            parts.append(con)
            pos[0] += 1
        return " ".join(parts) if style.startswith(">") else "\n".join(parts)

    root = parse_node(0)
    if pos[0] != len(lines):
        raise PhasesSyntaxError("残余不可解析行: %r" % (lines[pos[0]],))
    if not isinstance(root, dict):
        raise PhasesSyntaxError("根节点须为映射")
    return root


def load_phases(path=None):
    p = path or DEFAULT_YAML
    if not os.path.isfile(p):
        raise PhasesSyntaxError("phases.yaml 未找到: " + p)
    with open(p, encoding="utf-8") as f:
        return parse_yaml(f.read())


# ---------------------------------------------------------------- T2：schema 校验
FROZEN_CONSTANTS = {
    "restart_context_threshold": "0.75", "restart_every_n_rounds": "10",
    "storm_score_threshold_base": "0.5", "llm_association_quota": "5",
    "reversal_scan_quota": "3", "p4_sample_ratio": "0.2",
    "single_active_session": "true", "budget_dollars_enabled": "false",
}
EXTRA_TOOLS = {"tanyin-report", "tanyin-redact"}   # P5/P6 断言引用的非 ledger 入口


def _known_cmd(head, known):
    """断言命令存在性判定（PROTOCOL.md §1「双前缀注册均可查」语义）：
    先试原词，再试剥 ledger- 前缀词——yaml 断言首词统一带前缀，known 为基名集。"""
    if head in known:
        return True
    return head.startswith("ledger-") and head[len("ledger-"):] in known


def validate_phases(data, known):
    """契约 04 schema 校验（§10.3 静态验证③先行交付）。返回错误清单，空=合法。"""
    errs = []
    if str(data.get("format_version")) != "2":
        errs.append("format_version!=2")
    if [str(x) for x in (data.get("states") or [])] != list(GATE_ORDER):
        errs.append("states != 九门全序 %s" % (GATE_ORDER,))
    if data.get("initial") != "P0":
        errs.append("initial != P0")
    c = data.get("constants") or {}
    if set(c) != set(FROZEN_CONSTANTS):
        errs.append("constants 键集 != 冻结 8 项")
    for k, v in FROZEN_CONSTANTS.items():
        if str(c.get(k)) != v:
            errs.append("constants.%s=%r != 冻结值 %r" % (k, c.get(k), v))
    gates = data.get("gates") or {}
    if set(gates) != set(GATE_ORDER):
        errs.append("gates 键集 != 九门（缺/多: %s）"
                    % sorted(set(GATE_ORDER) ^ set(gates)))
    for g in GATE_ORDER:
        ex = ((gates.get(g) or {}).get("exit") or {}).get("assert") or []
        if not ex:
            errs.append("gates.%s.exit.assert 空" % g)
        for i, a in enumerate(ex, 1):
            head = str(a.get("cmd", "")).split()[:1]
            if not head or not _known_cmd(head[0], known):
                errs.append("gates.%s.exit.assert[%d] 命令不在命令面: %r" % (g, i, a.get("cmd")))
    if len(data.get("back_edges") or []) != 3:
        errs.append("back_edges != 3 条")
    ev = ((gates.get("P3") or {}).get("events") or {})
    if set(ev) != {"asset-added", "cred-obtained", "scope-amended"}:
        errs.append("P3.events 三事件键缺失: %s" % sorted(set(ev)))
    return errs


def cmd_validate(rest):
    path = None
    for tok in rest:
        if tok.startswith("--phases="):
            path = tok.split("=", 1)[1]
        else:
            sys.stderr.write("用法: tanyin-phases validate [--phases=<路径>]\n"); return 2
    try:
        data = load_phases(path)
    except PhasesSyntaxError as e:
        sys.stderr.write("环境问题: %s\n" % e); return 2
    from . import registry
    known = registry.all_commands() | EXTRA_TOOLS
    errs = validate_phases(data, known)
    if errs:
        print("FAIL\tphases.yaml 违规 %d 项" % len(errs))
        for e in errs:
            print("  " + e)
        return 1
    n = sum(len(((data["gates"][g] or {}).get("exit") or {}).get("assert") or [])
            for g in GATE_ORDER)
    print("PASS\tphases.yaml 契约04合法 gates=9 asserts=%d constants=8 back_edges=3" % n)
    return 0


def dispatch(sub, goal_dir, rest):
    if sub == "validate":
        return cmd_validate(rest)
    sys.stderr.write("未知子命令: " + sub + chr(10)); return 2
