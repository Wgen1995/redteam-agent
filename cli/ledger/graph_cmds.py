# -*- coding: utf-8 -*-
"""图查询三命令（批次 4 · 图谱驱动设计增补 71d3b7c）——只读确定性图运算。

节点=九表行 id；有向攻击可达边=edges.tsv（按记录方向）+凭据链
（CRED→scope_asset=cred:unlock；parent_cred 父→子=cred:derive）。
graph-neighbors 邻接展开（无向邻里，--edge-class ∈ {attack,asset,cred}，默认 all）；
graph-paths 可达路径枚举（--to 支持节点 id 或 scope-root=root-domain 资产集）；
graph-horizon 可达集×矩阵空格 join（喂 P3 派发：可达空格先行）。
确定性：邻接排序+BFS/DFS 定序+清单排序；输出摘要化（计数+清单）。
命令面 41→44：微版本勘误（同 G-1 先例；铁律 7 允许类=确定性账本运算，无攻击决策）。"""
from . import core
from .schemas import TABLES
from .query_cmds import (UsageError, usage_guard, parse_kv, latest_by, latest_matrix,
                         _cell, _idx)

TAB = chr(9)
DEFAULT_MAX_HOPS = 4
PATH_CAP = 50  # 防环组合爆炸：路径枚举上限（超出截断，#paths 记实收数）

_NODE_TABLES = (("goals.tsv", "goal"), ("scope.tsv", "scope"), ("intents.tsv", "intent"),
                ("facts.tsv", "fact"), ("findings.tsv", "finding"), ("assets.tsv", "asset"),
                ("approvals.tsv", "approval"), ("E-index.tsv", "evidence"), ("creds.tsv", "cred"))

_CLASS_KINDS = {"attack": {"attack", "proves", "evidences"},
                "asset": {"parent", "scope-rel"},
                "cred": set()}


def _label_class(label):
    """边类归属：attack/asset/cred/process（凭据链标签 cred:* 归 cred）。"""
    if label.startswith("cred:"):
        return "cred"
    for c, kinds in _CLASS_KINDS.items():
        if label in kinds:
            return c
    return "process"


def _build(s):
    """节点表+有向邻接（排序确定）。事件溯源表（intents/creds）按 latest 去重入图。"""
    nodes = {}
    for t, ty in _NODE_TABLES:
        for r in s.rows(t):
            nodes.setdefault(r[0], ty)
    adj = {n: [] for n in nodes}
    for r in s.rows("edges.tsv"):
        src = _cell(r, "edges.tsv", "source_id")
        dst = _cell(r, "edges.tsv", "target_id")
        if src in adj and dst in adj:
            adj[src].append((_cell(r, "edges.tsv", "kind"), dst))
    for r in latest_by(s.rows("creds.tsv"), "creds.tsv", ["id"]).values():
        cid = r[0]
        sa = _cell(r, "creds.tsv", "scope_asset")
        if sa and sa in adj:
            adj[cid].append(("cred:unlock", sa))
        pc = _cell(r, "creds.tsv", "parent_cred")
        if pc and pc in adj:
            adj[pc].append(("cred:derive", cid))
    for k in adj:
        adj[k].sort()
    return nodes, adj


def _undirected(adj):
    nbr = {n: [] for n in adj}
    for u, edges in adj.items():
        for label, v in edges:
            nbr[u].append((label, v, "out"))
            nbr[v].append((label, u, "in"))
    for k in nbr:
        nbr[k].sort()
    return nbr


def _int_arg(args, key, default):
    if key not in args:
        return default
    try:
        n = int(args[key])
    except (TypeError, ValueError):
        raise UsageError("--" + key + " 需整数")
    if n < 1:
        raise UsageError("--" + key + " 需正整数")
    return n


def _class_arg(args):
    c = args.get("edge-class", "all")
    if c not in ("all",) + tuple(_CLASS_KINDS):
        raise UsageError("--edge-class 仅 all|attack|asset|cred: " + c)
    return c


def h_graph_neighbors(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or "asset" not in args:
        raise UsageError("graph-neighbors 需 --asset=<id> [--depth=N] [--edge-class=…]")
    depth = _int_arg(args, "depth", 1)
    ecls = _class_arg(args)
    s = core.Session(goal_dir)
    nodes, adj = _build(s)
    if args["asset"] not in nodes:
        print("#count=0")  # 未知节点口径同 intent-status（§0.3 空集）
        return 0
    nbr = _undirected(adj)
    seen = {args["asset"]}
    frontier = [args["asset"]]
    rows = []
    for d in range(1, depth + 1):
        nxt = []
        for u in frontier:
            for label, v, direction in nbr[u]:
                if v in seen or (ecls != "all" and _label_class(label) != ecls):
                    continue
                seen.add(v)
                nxt.append(v)
                rows.append([str(d), v, nodes[v], label + ":" + direction])
        frontier = sorted(nxt)
    rows.sort(key=lambda r: (int(r[0]), r[1]))
    print("#count=%d" % len(rows))
    for r in rows:
        print(TAB.join(r))
    return 0


def _scope_root_targets(s, nodes):
    return {r[0] for r in s.rows("assets.tsv")
            if _cell(r, "assets.tsv", "type") == "root-domain" and r[0] in nodes}


def reachable_gap_cells(s, starts):
    """可达集 × 矩阵空格 join（graph-horizon/converge-check 单源，批次5 T7·G-28 前半）。

    starts=起点节点 id 集（converge 传 _scope_root_targets 的 scope-root 资产集；
    horizon 传 {--from}）。Ruling（R-T7-1）：计划片段签名 reachable_gap_cells(s) 固定
    起点=scope-root，与「h_graph_horizon 改调它、行为零变」冲突（horizon 起点=--from
    任意节点）——按行为零变优先将起点集参数化，语义两处共用同一 BFS+空格 join。
    返回 (reach, reach_gaps, unreach_gaps)：gaps=(attack_surface, vuln_class) 空格对
    （latest 行 state 空），按行键排序；reach/unreach 以「表面值 ∈ 可达资产值集」二分。
    """
    nodes, adj = _build(s)
    reach = {n for n in starts if n in nodes}
    frontier = sorted(reach)
    while frontier:
        nxt = []
        for u in frontier:
            for _label, v in adj[u]:
                if v not in reach:
                    reach.add(v)
                    nxt.append(v)
        frontier = sorted(nxt)
    ast_vals = {_cell(r, "assets.tsv", "value") for r in s.rows("assets.tsv")
                if r[0] in reach}
    gaps = sorted((_cell(r, "matrix.tsv", "attack_surface"),
                   _cell(r, "matrix.tsv", "vuln_class"))
                  for r in latest_matrix(s).values()
                  if _cell(r, "matrix.tsv", "state").strip() == "")
    reach_gaps = [g for g in gaps if g[0] in ast_vals]
    unreach_gaps = [g for g in gaps if g[0] not in ast_vals]
    return reach, reach_gaps, unreach_gaps


def h_graph_paths(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or "from" not in args or "to" not in args:
        raise UsageError("graph-paths 需 --from=<id> --to=<id|scope-root> [--max-hops=N]")
    max_hops = _int_arg(args, "max-hops", DEFAULT_MAX_HOPS)
    s = core.Session(goal_dir)
    nodes, adj = _build(s)
    start = args["from"]
    if args["to"] == "scope-root":
        targets = _scope_root_targets(s, nodes)
    else:
        targets = {args["to"]} & set(nodes)
    paths = []

    def dfs(node, path):
        if len(paths) >= PATH_CAP:
            return
        if node in targets:
            paths.append(list(path))
        if len(path) > max_hops:
            return
        for _label, v in adj[node]:
            if v in path:
                continue  # 简单路径（无重复节点）
            path.append(v)
            dfs(v, path)
            path.pop()

    if start in nodes:
        dfs(start, [start])
    paths.sort(key=lambda p: TAB.join(p))
    print("#paths=%d%s" % (len(paths), "（截断至 %d）" % PATH_CAP if len(paths) >= PATH_CAP else ""))
    for p in paths:
        print("->".join(p))
    return 0


def h_graph_horizon(goal_dir, rest):
    args, pos = parse_kv(rest)
    if pos or "from" not in args:
        raise UsageError("graph-horizon 需 --from=<id>")
    s = core.Session(goal_dir)
    nodes, _adj = _build(s)
    start = args["from"]
    # 批次5 T7：BFS+空格 join 抽为 reachable_gap_cells 单源（converge-check 同函数）——
    # 起点={--from}，输出与抽取前逐字节一致（金样 graph-graph-horizon.norm 钉）。
    reach, gaps, _unreach = reachable_gap_cells(s, {start})
    reach_rows = sorted((n, nodes[n]) for n in reach)
    print("#reachable=%d" % len(reach_rows))
    for n, ty in reach_rows:
        print(n + TAB + ty)
    print("#gaps=%d" % len(gaps))
    for surface, vclass in gaps:
        print(surface + TAB + vclass)
    return 0


HANDLERS = {name: usage_guard(fn) for name, fn in {
    "graph-neighbors": h_graph_neighbors,
    "graph-paths": h_graph_paths,
    "graph-horizon": h_graph_horizon,
}.items()}
