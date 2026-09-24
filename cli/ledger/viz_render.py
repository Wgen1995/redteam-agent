# -*- coding: utf-8 -*-
"""viz 数据岛构建+HTML 渲染（批4 T11；R4 零依赖 SVG——确定性分层布局）。

只读 13 表+timeline；数据岛全排序确定性；HTML 内联 vanilla JS（过滤/搜索/面板切换/节点详情）。
追加件（fb72cd5）：findings 实时流投影——最新 N 条（时间/资产/类型/severity/状态），
high/critical 置顶标记；确定性输出可金样化（--data-only 金样面）。"""
import json

from . import authz_matrix
from .schemas import TABLES

EDGE_STYLE = {"attack": "gold", "cross_ref": "dashed", "supersedes": "dotted",
              "scope-rel": "gray"}          # 其余六边 solid
NODE_TABLES = (("goals.tsv", "G"), ("intents.tsv", "INT"), ("assets.tsv", "AST"),
               ("facts.tsv", "F"), ("findings.tsv", "FD"), ("E-index.tsv", "EV"), ("creds.tsv", "CRED"))
LAYER = {"G": 0, "INT": 1, "AST": 2, "CRED": 2, "F": 3, "FD": 4, "EV": 5}
FINDING_STREAM_N = 20                 # 追加件：实时流最新 N 条（作战视图，禁全量回灌同精神）
HIGH_SEVERITIES = ("高", "high", "critical")   # 置顶标记档（impact 词表 {高,中,低}+英文容错）


def build_island(s):
    counts = {t: len(s.rows(t)) for t in sorted(TABLES)}
    conf = {}
    ti = TABLES["findings.tsv"]
    for r in s.rows("findings.tsv"):
        key = "%s×%s" % (r[ti.index("confidence")], r[ti.index("impact")])
        conf[key] = conf.get(key, 0) + 1
    tle = TABLES["timeline.tsv"]
    phases = [r[tle.index("event")] for r in s.rows("timeline.tsv")
              if r[tle.index("event")].startswith("gate-exit:")]
    nodes = []
    for t, prefix in NODE_TABLES:
        for r in sorted(s.rows(t), key=lambda r: r[0]):
            cand = (t == "intents.tsv" and r[TABLES[t].index("status")] == "candidate")
            nodes.append({"id": r[0], "kind": prefix, "layer": LAYER[prefix],
                          "label": r[0], "candidate": cand})
    te = TABLES["edges.tsv"]
    edges = [{"src": r[te.index("source_id")], "dst": r[te.index("target_id")],
              "kind": r[te.index("kind")]} for r in sorted(s.rows("edges.tsv"), key=lambda r: r[0])]
    unconsumed = [r[0] for r in sorted(s.rows("facts.tsv"), key=lambda r: r[0])
                  if not any(e[te.index("kind")] == "derived_from"
                             and e[te.index("source_id")] == r[0]
                             for e in s.rows("edges.tsv"))]
    origins = {}
    for r in s.rows("intents.tsv"):
        o = r[TABLES["intents.tsv"].index("origin")]
        origins[o] = origins.get(o, 0) + 1
    cleanup_open = sum(1 for r in s.rows("timeline.tsv")
                       if r[tle.index("revert_cmd")] and not r[tle.index("event")].startswith("reverted"))
    # 统计栏扩展（模板渲染消费）：矩阵非空格率/攻击链数/收敛计数/预算汇总——全确定性
    tme = TABLES["matrix.tsv"]
    matrix_set = sum(1 for r in s.rows("matrix.tsv") if r[tme.index("state")].strip())
    attack_edges = sum(1 for e in s.rows("edges.tsv") if e[te.index("kind")] == "attack")
    converged = sum(1 for r in s.rows("timeline.tsv") if "converge" in r[tle.index("event")])
    tbe = TABLES["budget.tsv"]
    budget = {"token": 0, "requests": 0, "hours": 0, "dollars": 0}
    for r in s.rows("budget.tsv"):
        for k, col in (("token", "token_delta"), ("requests", "requests_delta"),
                       ("hours", "hours_delta"), ("dollars", "dollars_delta")):
            try:
                budget[k] += float(r[tbe.index(col)] or 0)
            except ValueError:
                pass
    return {"stats": {"counts": counts, "confidence": conf,
                      "matrix_rows": len(s.rows("matrix.tsv")),
                      "matrix_set": matrix_set, "attack_edges": attack_edges,
                      "converged": converged, "budget": budget},
            "phases": phases,
            "graph": {"nodes": nodes, "edges": edges, "edge_style": EDGE_STYLE},
            "rightpanel": {"unconsumed_facts": unconsumed, "storm_origins": origins,
                           "cleanup_open": cleanup_open},
            "authz_matrix": authz_matrix.coverage(s),
            "findings_stream": _finding_stream(s)}


def _finding_stream(s):
    """追加件（fb72cd5）：最新 N 条 findings，high/critical 稳定置顶（段内按新近降序）。"""
    tf = TABLES["findings.tsv"]
    ta = TABLES["assets.tsv"]
    ast_value = {r[0]: r[ta.index("value")] for r in s.rows("assets.tsv")}
    rows = sorted(s.rows("findings.tsv"),
                  key=lambda r: (r[tf.index("created")], r[0]))[-FINDING_STREAM_N:][::-1]   # 最新在前
    items = []
    for r in rows:
        sev = r[tf.index("impact")]
        items.append({"id": r[0], "time": r[tf.index("created")],
                      "asset": ast_value.get(r[tf.index("affected_asset_id")],
                                             r[tf.index("affected_asset_id")]),
                      "type": r[tf.index("vuln_ref")], "severity": sev,
                      "status": r[tf.index("status")],
                      "pinned": sev in HIGH_SEVERITIES})
    pinned = [it for it in items if it["pinned"]]
    return {"n": FINDING_STREAM_N, "pinned_high": len(pinned),
            "items": pinned + [it for it in items if not it["pinned"]]}


def render_html(s):
    payload = json.dumps(build_island(s), ensure_ascii=False, sort_keys=True)
    # 数据岛嵌入防 </script> 提前闭合（JSON 合法转义 /）
    return TEMPLATE.replace("__TANYIN_DATA__", payload.replace("</", "<\/"))


TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>探隐 session-viz · 交战区作战视图</title>
<style>
 body{font:13px/1.5 "PingFang SC","Microsoft YaHei",sans-serif;margin:0;background:#11151c;color:#d7dde6}
 header{padding:10px 16px;background:#171d27;border-bottom:1px solid #2a3342}
 h1{font-size:15px;margin:0 0 8px}
 #stats{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12px}
 .badge{display:inline-block;padding:0 6px;border-radius:8px;margin-right:4px}
 .C1{background:#1d5c2e}.C2{background:#6b5a12}.C3{background:#3a3f47}.dead{background:#6b1212}
 .bar{height:8px;background:#2a3342;border-radius:4px;overflow:hidden;display:inline-block;vertical-align:middle;width:140px}
 .bar>i{display:block;height:100%;background:#4f8cff}
 main{display:flex;gap:10px;padding:10px 16px}
 #left{flex:1 1 auto;min-width:0}
 section{background:#171d27;border:1px solid #2a3342;border-radius:6px;margin-bottom:10px;padding:8px 10px}
 h2{font-size:13px;margin:0 0 6px;color:#9fb3d1}
 #stream-list{max-height:180px;overflow:auto}
 #stream-list table{border-collapse:collapse;width:100%}
 #stream-list td,#stream-list th{padding:2px 8px;border-bottom:1px solid #232b38;text-align:left}
 tr.pinned{color:#ff9f43;font-weight:600}
 tr.pinned td:first-child:before{content:"▲";}
 #phases{display:flex;flex-wrap:wrap;gap:4px}
 #phases span{padding:2px 8px;border:1px solid #2a3342;border-radius:10px;font-size:11px}
 #phases span.cur{border-color:#4f8cff;color:#4f8cff}
 #controls{margin:6px 0}
 #controls button{margin-right:4px;background:#202939;color:#d7dde6;border:1px solid #2a3342;border-radius:4px;padding:2px 8px;cursor:pointer}
 #controls button.on{border-color:#4f8cff;color:#4f8cff}
 #controls input{background:#202939;border:1px solid #2a3342;color:#d7dde6;border-radius:4px;padding:2px 6px}
 svg{width:100%;height:420px;background:#0d1117;border-radius:4px}
 aside{flex:0 0 340px}
 aside ul{margin:4px 0 8px;padding-left:18px}
 .node{cursor:pointer}
 .node.candidate{opacity:.45}
 table.mx{border-collapse:collapse;font-size:11px}
 table.mx td,table.mx th{border:1px solid #2a3342;padding:1px 6px}
 #detail{min-height:48px;color:#9fb3d1}
</style>
</head>
<body>
<header>
 <h1>探隐 session-viz（projector 型投影 · 零依赖 SVG · 只读账本）</h1>
 <div id="stats"></div>
</header>
<main>
 <div id="left">
  <section><h2>findings 实时流（最新 N 条 · high/critical 置顶▲）</h2><div id="stream-list"></div></section>
  <section><h2>Pipeline 时间轴（gate-exit 序 · 当前=最后一门）</h2><div id="phases"></div></section>
  <section><h2>图谱（分层布局 · attack 金/cross_ref 虚/supersedes 点/candidate 半透明）</h2>
   <div id="controls">
    <button class="on" data-kind="*">全部</button><button data-kind="G">G</button><button data-kind="INT">INT</button><button data-kind="AST">AST</button><button data-kind="CRED">CRED</button><button data-kind="F">F</button><button data-kind="FD">FD</button><button data-kind="EV">EV</button>
    <input id="q" placeholder="搜索节点 id…">
    <button id="layout">布局：分层/力导向</button>
   </div>
   <svg id="graph" xmlns="http://www.w3.org/2000/svg"></svg>
   <div id="detail">点击节点查看详情</div>
  </section>
 </div>
 <aside>
  <section><h2>右面板 · 未消费 fact</h2><ul id="unconsumed"></ul></section>
  <section><h2>风暴 origin</h2><ul id="origins"></ul></section>
  <section><h2>清理清单核销（未核销 <span id="cleanup">0</span>）</h2></section>
  <section><h2>身份矩阵 role×endpoint（■=covered）</h2><div id="authz"></div></section>
 </aside>
</main>
<script id="tanyin-data" type="application/json">__TANYIN_DATA__</script>
<script>
var D = JSON.parse(document.getElementById("tanyin-data").textContent);
function el(t, cls, text) {
  var e = document.createElement(t);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function renderStats() {
  var box = document.getElementById("stats"), st = D.stats;
  var c = Object.keys(st.counts).map(function (t) { return t + "=" + st.counts[t]; }).join("  ");
  box.appendChild(el("span", null, c));
  Object.keys(st.confidence).sort().forEach(function (k) {
    var m = k.split("×"), b = el("span", "badge " + (m[0] === "C1" ? "C1" : m[0] === "C2" ? "C2" : m[0] === "C3" ? "C3" : "dead"));
    b.textContent = k + "×" + st.confidence[k];
    box.appendChild(b);
  });
  box.appendChild(el("span", null, "攻击链=" + st.attack_edges));
  box.appendChild(el("span", null, "矩阵=" + st.matrix_set + "/" + st.matrix_rows));
  box.appendChild(el("span", null, "converge 事件=" + st.converged));
  var bar = el("span", "bar"), i = el("i");
  i.style.width = Math.min(100, st.budget.requests) + "%";
  bar.appendChild(i);
  box.appendChild(el("span", null, "预算 requests≈" + st.budget.requests));
  box.appendChild(bar);
}
function renderStream() {
  var box = document.getElementById("stream-list"), tb = el("table");
  var head = tb.insertRow();
  ["置顶", "时间", "资产", "类型", "severity", "状态", "id"].forEach(function (h) { head.appendChild(el("th", null, h)); });
  D.findings_stream.items.forEach(function (it) {
    var tr = tb.insertRow();
    if (it.pinned) tr.className = "pinned";
    [it.pinned ? "高" : "", it.time, it.asset, it.type || "—", it.severity, it.status, it.id]
      .forEach(function (v) { tr.insertCell().textContent = v; });
  });
  box.appendChild(tb);
}
function renderPhases() {
  var box = document.getElementById("phases");
  D.phases.forEach(function (p, i) {
    var m = p.split(/\s+/);
    box.appendChild(el("span", i === D.phases.length - 1 ? "cur" : null, m[0]));
  });
}
var curKind = "*", curLayout = 0;
function layoutPos(nodes) {
  var pos = {}, byLayer = {};
  nodes.forEach(function (n) { (byLayer[n.layer] = byLayer[n.layer] || []).push(n); });
  Object.keys(byLayer).forEach(function (l) {
    byLayer[l].sort(function (a, b) { return a.id < b.id ? -1 : 1; })
      .forEach(function (n, col) { pos[n.id] = [200 + n.layer * 160, 40 + col * 36]; });
  });
  if (!curLayout) return pos;
  // 力导向（纯计算：确定性迭代，无随机源）
  nodes.forEach(function (n) {
    pos[n.id] = (pos[n.id] || [200, 40]).slice();
  });
  for (var it = 0; it < 40; it++) {
    nodes.forEach(function (a) {
      var fx = 0, fy = 0;
      nodes.forEach(function (b) {
        if (a === b) return;
        var dx = pos[a.id][0] - pos[b.id][0], dy = pos[a.id][1] - pos[b.id][1];
        var d2 = dx * dx + dy * dy + 1;
        fx += dx / d2 * 800; fy += dy / d2 * 800;
      });
      pos[a.id][0] += Math.max(-12, Math.min(12, fx * 0.05));
      pos[a.id][1] += Math.max(-12, Math.min(12, fy * 0.05));
    });
  }
  return pos;
}
function svgLayered() {
  var svg = document.getElementById("graph");
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  var NS = "http://www.w3.org/2000/svg";
  var q = document.getElementById("q").value;
  var nodes = D.graph.nodes.filter(function (n) {
    return (curKind === "*" || n.kind === curKind) && (!q || n.id.indexOf(q) >= 0);
  });
  var ids = {}; nodes.forEach(function (n) { ids[n.id] = 1; });
  var pos = layoutPos(nodes);
  D.graph.edges.forEach(function (e) {
    if (!ids[e.src] || !ids[e.dst]) return;
    var l = document.createElementNS(NS, "line");
    l.setAttribute("x1", pos[e.src][0]); l.setAttribute("y1", pos[e.src][1]);
    l.setAttribute("x2", pos[e.dst][0]); l.setAttribute("y2", pos[e.dst][1]);
    var st = D.graph.edge_style[e.kind] || "";
    l.setAttribute("stroke", st === "gold" ? "#d4a017" : st === "gray" ? "#555c66" : "#4f8cff");
    if (st === "dashed") l.setAttribute("stroke-dasharray", "6 4");
    if (st === "dotted") l.setAttribute("stroke-dasharray", "2 3");
    svg.appendChild(l);
  });
  nodes.forEach(function (n) {
    var g = document.createElementNS(NS, "g"), t = document.createElementNS(NS, "text");
    t.setAttribute("x", pos[n.id][0] + 8); t.setAttribute("y", pos[n.id][1] + 4);
    t.setAttribute("fill", n.candidate ? "#7c8794" : "#d7dde6");
    t.textContent = n.kind + ":" + n.id;
    g.appendChild(t);
    g.setAttribute("class", "node" + (n.candidate ? " candidate" : ""));
    g.onclick = function () {
      document.getElementById("detail").textContent =
        "节点 " + n.id + " · 类型 " + n.kind + " · 层 " + n.layer + (n.candidate ? " · candidate（半透明）" : "");
    };
    svg.appendChild(g);
  });
}
function renderPanel() {
  var u = document.getElementById("unconsumed");
  (D.rightpanel.unconsumed_facts.length ? D.rightpanel.unconsumed_facts : ["（无）"])
    .forEach(function (f) { u.appendChild(el("li", null, f)); });
  var o = document.getElementById("origins");
  Object.keys(D.rightpanel.storm_origins).sort().forEach(function (k) {
    o.appendChild(el("li", null, k + " ×" + D.rightpanel.storm_origins[k]));
  });
  document.getElementById("cleanup").textContent = D.rightpanel.cleanup_open;
  var mx = D.authz_matrix, tb = el("table", "mx");
  if (!mx.endpoints || !Object.keys(mx.endpoints).length) { document.getElementById("authz").textContent = "（无 endpoint 资产）"; return; }
  var head = tb.insertRow();
  head.appendChild(el("th", null, "endpoint＼role"));
  mx.roles.forEach(function (r) { head.appendChild(el("th", null, r)); });
  Object.keys(mx.endpoints).sort().forEach(function (ep) {
    var tr = tb.insertRow();
    tr.insertCell().textContent = ep;
    mx.roles.forEach(function (r) { tr.insertCell().textContent = mx.endpoints[ep].roles[r].covered ? "■" : "□"; });
  });
  var cap = el("div", null, "覆盖 " + mx.coverage);
  var box = document.getElementById("authz");
  box.appendChild(tb); box.appendChild(cap);
}
renderStats(); renderStream(); renderPhases(); renderPanel(); svgLayered();
Array.prototype.forEach.call(document.querySelectorAll("#controls button[data-kind]"), function (b) {
  b.onclick = function () {
    Array.prototype.forEach.call(document.querySelectorAll("#controls button[data-kind]"), function (x) { x.className = ""; });
    b.className = "on"; curKind = b.getAttribute("data-kind"); svgLayered();
  };
});
document.getElementById("q").oninput = svgLayered;
document.getElementById("layout").onclick = function () {
  curLayout = curLayout ? 0 : 1;
  this.textContent = curLayout ? "布局：力导向/分层" : "布局：分层/力导向";
  svgLayered();
};
</script>
</body>
</html>
"""
