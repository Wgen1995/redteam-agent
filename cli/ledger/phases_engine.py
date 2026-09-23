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


# ---------------------------------------------------------------- T3：gate 断言执行器
# 协议=phases/PROTOCOL.md §1（判定表逐行对应）。两处计划↔实现裁决（HANDOFF 记账）：
# Ruling A：yaml 断言首词统一带 ledger- 前缀而 validate/verify-chain 等 builtin 只注册
#   无前缀基名——lookup 按 §1「双前缀注册均可查」语义归一（先原词，再剥前缀），否则
#   P0 断言 ledger-validate 会误判「未知命令」、计划自己的 test_gate_p0 用例必红。
# Ruling B：EXTRA_TOOLS（tanyin-report/tanyin-redact）非 ledger 命令、registry 不可达——
#   按 §1 判定表末行语义（工具未交付=ENV-HALT 退出 2，非门禁失败），不经 gate-fail 落账。
SKIP_MARK = "批次 4 前=SKIP"


def _normalize_argv(tokens):
    """空格式旗标归一：`--k v`（v 不以 -- 开头）合并为 `--k=v`；裸旗标原样传递。"""
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith("--") and "=" not in t and i + 1 < len(tokens) \
                and not tokens[i + 1].startswith("--"):
            out.append(t + "=" + tokens[i + 1]); i += 2
        else:
            out.append(t); i += 1
    return out


def _current_gate(s):
    """从 gate-exit 序推导当前门：无事件→P0；最大下标门为 P6→END；否则下一门。
    T5 rebuild-state / T6 restart / T7 resume-kit 复用（计划 Interfaces 声明）。"""
    seq, _ = s.gate_exit_seq()
    if not seq:
        return "P0"
    top = max(GATE_ORDER.index(g) for g in seq)
    return "END" if GATE_ORDER[top] == "P6" else GATE_ORDER[top + 1]


def _lookup_cmd(head):
    from . import registry
    h = registry.lookup(head)
    if h is None and head.startswith("ledger-"):
        h = registry.lookup(head[len("ledger-"):])
    return h


def _judge(expect, cmdline, code, out, err, s):
    name = cmdline.split()[0]
    if SKIP_MARK in expect:
        return "skip", "expect 载 SKIP（批次 4 转强制）"
    if name.endswith("converge-check"):
        tok = out.strip().splitlines()[0].strip() if out.strip() else ""
        if code == 0 and tok in ("converged", "budget-exhausted"):
            return "pass", ("mode=degraded" if tok == "budget-exhausted" else "")
        return "fail", "converge-check 输出=%r" % tok
    if name.endswith("matrix-gaps") and "--baseline" in cmdline:
        m = re.search(r"#baseline_rows=(\d+)", out)
        if code == 0 and "covered=true" in out and m and int(m.group(1)) > 0:
            return "pass", ""
        return "fail", "baseline=%s" % out.strip()[:60]
    if name.endswith("matrix-freeze") and code == 1:
        if "already-frozen" in (err + out) and any(
                r[core.TABLES["timeline.tsv"].index("event")].startswith("matrix-freeze")
                for r in s.rows("timeline.tsv")):
            return "pass", "already-frozen 幂等"
    if code == 2:
        return "env", (err or out).strip()[:80]
    return ("pass" if code == 0 else "fail"), (err or out).strip()[:80]


def _append_event(goal_dir, phase, event, ts):
    from . import registry
    h = registry.lookup("append-timeline")
    buf_o, buf_e = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_o), redirect_stderr(buf_e):
        code = h(goal_dir, ["--actor=总控", "--phase=" + phase,
                            "--event=" + event, "--timestamp=" + ts])
    if code != 0:
        raise RuntimeError("append-timeline 失败: " + buf_e.getvalue())


def run_gate(goal_dir, phase, ts, phases_path=None):
    data = load_phases(phases_path)
    from . import registry
    errs = validate_phases(data, registry.all_commands() | EXTRA_TOOLS)
    if errs:
        sys.stderr.write("环境问题: phases.yaml 违规 %d 项\n" % len(errs)); return 2
    if phase not in GATE_ORDER:
        sys.stderr.write("用法错误: --phase 不在九门\n"); return 2
    if not ts:
        sys.stderr.write("用法错误: --timestamp 必填（ISO8601）\n"); return 2
    s = core.Session(goal_dir)
    seq, _ = s.gate_exit_seq()
    if phase in seq:
        print("OK" + chr(9) + "gate:%s already-passed" % phase); return 0
    for prev in GATE_ORDER[:GATE_ORDER.index(phase)]:
        if prev not in seq:
            print("REJECT" + chr(9) + "gate" + chr(9) + "前置门未过: " + prev)
            return 1
    asserts = data["gates"][phase]["exit"]["assert"]
    skipped, degraded = 0, False
    for a in asserts:
        cmdline, expect = str(a.get("cmd", "")), str(a.get("expect", ""))
        tokens = shlex.split(cmdline)
        # Ruling C（写类断言时间戳注入）：matrix-freeze 是 yaml 断言集里唯一的写类命令
        # （PROTOCOL.md §1.4「经自身 handler 落账」），其 --timestamp 必填而 yaml cmd
        # 不携带——注入门级确定性时间戳（禁 datetime.now 纪律）。读类命令不注入
        # （converge-check 等「无参数」命令会 UsageError→误 ENV-HALT）。
        if tokens[0].endswith("matrix-freeze") \
                and not any(t.startswith("--timestamp=") for t in tokens[1:]):
            tokens = tokens + ["--timestamp=" + ts]
        if tokens[0] in EXTRA_TOOLS:
            print("ENV-HALT gate:%s assert=%s 工具未交付（批次 6）" % (phase, tokens[0]))
            return 2
        h = _lookup_cmd(tokens[0])
        if h is None:
            _append_event(goal_dir, phase, "gate-fail:%s assert=%s reason=未知命令" % (phase, tokens[0]), ts)
            print("FAIL gate:%s 未知命令 %s" % (phase, tokens[0])); return 1
        buf_o, buf_e = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_o), redirect_stderr(buf_e):
            code = h(goal_dir, _normalize_argv(tokens[1:]))
        st, detail = _judge(expect, cmdline, code, buf_o.getvalue(), buf_e.getvalue(), s)
        if st == "env":
            print("ENV-HALT gate:%s assert=%s %s" % (phase, tokens[0], detail)); return 2
        if st == "skip":
            skipped += 1; continue
        if "mode=degraded" in detail:
            degraded = True
        if st == "fail":
            _append_event(goal_dir, phase,
                          "gate-fail:%s assert=%s reason=%s" % (phase, tokens[0], detail or "exit!=0"), ts)
            print("FAIL gate:%s assert=%s %s" % (phase, tokens[0], detail)); return 1
    ev = "gate-exit:%s asserts=%d result=PASS" % (phase, len(asserts))
    if skipped:
        ev += " skip=%d" % skipped
    if degraded:
        ev += " mode=degraded"
    _append_event(goal_dir, phase, ev, ts)
    print("OK" + chr(9) + "gate:%s %s" % (phase, ev))
    return 0


def cmd_gate(goal_dir, rest):
    phase = ts = None
    for tok in rest:
        if tok.startswith("--phase="):
            phase = tok.split("=", 1)[1]
        elif tok.startswith("--timestamp="):
            ts = tok.split("=", 1)[1]
        else:
            sys.stderr.write("用法: tanyin-phases gate --goal-dir D --phase <门> "
                             "[--timestamp=T]\n"); return 2
    return run_gate(goal_dir, phase, ts, None)


# ------------------------------------- T3 追加件：分母就绪门（PROTOCOL.md §4）
DENOM_CLASSES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8")
DENOM_CLASS_BY_TYPE = {
    "root-domain": "A1", "subdomain": "A1",      # 标识层
    "ip": "A2",                                    # 网络层
    "service": "A3",                               # 服务层
    "app": "A4", "endpoint": "A4",                 # 应用层
    "source-code": "A6",                           # 代码与物料（A5/A7 无对应 type，探知项）
}
DENOM_NA_PREFIX = "asset-class:"     # 不适用理由：fact(kind=info, target=asset-class:A<k>)
DENOM_UNVERIFIED_MARK = "unverified"  # 单源未证标记：assets.meta
DENOM_EXTRAPOLATION_MARKS = ("extrapolated", "外推")   # A8 外推资产标记：assets.meta
DENOM_QUEUE_STATUS = "pending"        # 在队列
DENOM_DIG_KIND = "recon"              # 继续挖任务类
DENOM_INTEGRATION_KINDS = ("parent", "attack", "scope-rel")   # 图谱整合边
DENOM_IN_SCOPE_VALUES = ("1", "in_scope", "true")


def _cell(table, row, field):
    return row[core.TABLES[table].index(field)]


def denominator_ready(goal_dir):
    """分母就绪门（完备性设计 §1.3①③②三断言，matrix freeze 前置检查）。
    只读账本（facts/assets/edges/intents），零落账；读侧约定=phases/PROTOCOL.md §4。
    返回 (fails, stats)：fails 空=就绪。"""
    s = core.Session(goal_dir)
    arows, frows = s.rows("assets.tsv"), s.rows("facts.tsv")
    irows, erows = s.rows("intents.tsv"), s.rows("edges.tsv")

    def meta_has(r, mark):
        return mark in _cell("assets.tsv", r, "meta")

    def is_extrapolated(r):
        return any(meta_has(r, m) for m in DENOM_EXTRAPOLATION_MARKS)

    def sources_of(value):
        return len({_cell("facts.tsv", f, "intent_id") for f in frows
                    if _cell("facts.tsv", f, "target") == value
                    and _cell("facts.tsv", f, "intent_id")})

    def bound_intent(aid, value, statuses=None):
        for it in irows:
            if statuses and _cell("intents.tsv", it, "status") not in statuses:
                continue
            if _cell("intents.tsv", it, "dedup_key").startswith(aid + "+"):
                return True
            if value in _cell("intents.tsv", it, "title") \
                    or value in _cell("intents.tsv", it, "detail"):
                return True
        return False

    def integrated(aid):
        for e in erows:
            if _cell("edges.tsv", e, "kind") not in DENOM_INTEGRATION_KINDS:
                continue
            if aid in (_cell("edges.tsv", e, "source_id"),
                       _cell("edges.tsv", e, "target_id")):
                return True
        return False

    na_classes = set()
    for f in frows:
        t = _cell("facts.tsv", f, "target")
        k = t[len(DENOM_NA_PREFIX):] if t.startswith(DENOM_NA_PREFIX) else ""
        if k in DENOM_CLASSES and _cell("facts.tsv", f, "detail"):
            na_classes.add(k)

    class_count = dict.fromkeys(DENOM_CLASSES, 0)
    for a in arows:
        c = DENOM_CLASS_BY_TYPE.get(_cell("assets.tsv", a, "type"))
        if c:
            class_count[c] += 1
        if is_extrapolated(a):
            class_count["A8"] += 1   # A8 关联外推资产（界外也记，设计 §1.1）

    fails = []
    stats = {"assets": len(arows), "in_scope": 0, "sources_ok": 0,
             "classes_ok": 0, "extrapolated": 0, "dangling": 0}
    for a in arows:
        if _cell("assets.tsv", a, "in_scope") not in DENOM_IN_SCOPE_VALUES:
            continue   # 界外资产不入①（触发器目录：界外资产→记录不测）
        stats["in_scope"] += 1
        aid, value = _cell("assets.tsv", a, "id"), _cell("assets.tsv", a, "value")
        n_src = sources_of(value)
        unv = meta_has(a, DENOM_UNVERIFIED_MARK)
        dig = unv and bound_intent(aid, value, statuses=(DENOM_QUEUE_STATUS,))
        if n_src >= 2 or dig:
            stats["sources_ok"] += 1
        else:
            fails.append("①来源 %s %s 来源数=%d<2 unverified=%s 在队列继续挖=%s"
                         % (aid, value, n_src, "是" if unv else "否",
                            "是" if dig else "否"))
    for c in DENOM_CLASSES:
        if class_count[c]:
            stats["classes_ok"] += 1
        elif c not in na_classes:
            fails.append("②类空 %s 类空且无不适用理由"
                         "（fact target=asset-class:%s detail=理由，或补该类资产）" % (c, c))
    for a in arows:
        if not is_extrapolated(a):
            continue
        stats["extrapolated"] += 1
        aid, value = _cell("assets.tsv", a, "id"), _cell("assets.tsv", a, "value")
        if sources_of(value) or bound_intent(aid, value) or integrated(aid):
            continue   # 已处理：有采集 fact/绑定 intent（任意状态）/图谱整合边
        stats["dangling"] += 1
        fails.append("③悬空 %s %s 外推节点未处理（无采集 fact/绑定 intent/图谱整合边）"
                     % (aid, value))
    return fails, stats


def cmd_denominator_ready(goal_dir, rest):
    if rest:
        sys.stderr.write("用法: tanyin-phases denominator-ready --goal-dir D（只读，无参数）\n")
        return 2
    fails, st = denominator_ready(goal_dir)
    if fails:
        print("FAIL" + chr(9) + "denominator-ready" + chr(9)
              + "违规 %d 项（分母就绪门：matrix freeze 前置检查）" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("PASS" + chr(9) + "denominator-ready" + chr(9)
          + "assets=%d in_scope=%d sources_ok=%d classes_ok=%d/8 extrapolated=%d dangling=%d"
          % (st["assets"], st["in_scope"], st["sources_ok"], st["classes_ok"],
             st["extrapolated"], st["dangling"]))
    return 0


# ------------------------------------------------------- T5：rebuild-state 对账重建
# 恢复协议「先对账再干活」的修复臂：state-rebuild FAIL（撕裂态 B=timeline 领先 /
# C=state.md 缺失 / A=tmp 残留）后，以账本（第一事实源）为准重建 state.md。
# 重建即锁释放（session=rebuilt/released）——接管者走 checkpoint 重取锁，防双活。

def rebuild_state(goal_dir, ts, note=""):
    s = core.Session(goal_dir)
    ok, bad = s.verify_chain()
    if not ok:
        print("FAIL rebuild-state: timeline 断链行=%d——链断不可自愈，人工处置（halt）" % bad)
        return 1
    from . import state_md
    gate = _current_gate(s)
    # phase 域只收九门枚举或空（v2 冻结格式）：P0=尚未过任何门、END=P6 已收官，
    # 均为九门工作词汇之外的档位语义，不进 phase 域（否则 parse_state 判损坏，
    # 重建后 state-rebuild 反不 PASS——违背「rebuild 后对账一致」意图）
    fields = {
        "revision": str(len(s.rows("timeline.tsv"))),
        "goal": s.rows("goals.tsv")[0][0] if s.rows("goals.tsv") else "",
        "phase": "" if gate in ("P0", "END") else gate,
        "round": "0",
        "session": "rebuilt",
        "session_status": "released",   # 重建=锁必须释放（防双活；接管者走 checkpoint/restart 重取锁）
        "spawn": "manual",
        "updated": ts,
        "resume_kit": "resume-kit.md",
        "snapshot": state_md.snapshot_from_session(s),
    }
    handoff = ["rebuilt from ledger @ " + ts] + ([note] if note else [])
    tmp = os.path.join(goal_dir, "state.md.tmp")
    if os.path.exists(tmp):
        os.remove(tmp)   # 撕裂态 A 清理：tmp 残留一并扫除
    try:
        state_md.write_state(os.path.join(goal_dir, "state.md"), fields, handoff)
    except ValueError as e:
        print("FAIL rebuild-state: " + str(e))
        return 1
    print("OK\trebuild-state\trevision=%s" % fields["revision"])
    return 0


def cmd_rebuild_state(goal_dir, rest):
    ts, note = None, ""
    for tok in rest:
        if tok.startswith("--timestamp="):
            ts = tok.split("=", 1)[1]
        elif tok.startswith("--note="):
            note = tok.split("=", 1)[1]
        else:
            sys.stderr.write("用法: tanyin-phases rebuild-state --goal-dir D "
                             "--timestamp=T [--note=文本]\n"); return 2
    if not ts:
        sys.stderr.write("用法错误: --timestamp 必填（ISO8601）\n"); return 2
    return rebuild_state(goal_dir, ts, note)


def dispatch(sub, goal_dir, rest):
    if sub == "validate":
        return cmd_validate(rest)
    if sub == "gate":
        return cmd_gate(goal_dir, rest)
    if sub == "denominator-ready":
        return cmd_denominator_ready(goal_dir, rest)
    if sub == "rebuild-state":
        return cmd_rebuild_state(goal_dir, rest)
    sys.stderr.write("未知子命令: " + sub + chr(10)); return 2
