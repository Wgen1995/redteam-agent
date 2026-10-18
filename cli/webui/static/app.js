/* GraphLed 共享壳 app.js（UI-1 总装舰独写）——全站导航网 + nav.push 自注册面。
 *
 * 契约（各舰 static/pages/*.html 已钉「守卫式消费」）：
 *   ① 每页 <script src="/static/app.js"> 引本壳；壳渲染浮动导航钮+全站页网
 *      （组序=panorama/graphled-console-prototype.html 终态六组形：12 级灰阶+
 *      单强调色+mono 数字；样式全内联自足，不依赖任何页内 CSS/零框架零 CDN）。
 *   ② window.nav.push({id,label|title,group}) 自注册：本页入网并标当前页
 *      （label/title 两种拼写都收——各舰成文不一，不逼改兄弟舰）。
 *   ③ 导航跳转自动携带 ?battle=N（任务上下文不断链）；壳异常不殃及页面
 *      （try/catch 全包裹——本壳缺席/炸掉时各页独立可用）。
 */
"use strict";
var nav = (function () {
  var ACCENT = "#3ddc97";
  // 全站页网：[组, 名称, 路径]——驾驶舱六面（功能27 蓝图 25页砍到6面）顶置：
  // 首页/任务/漏洞/知识库/收件箱/设置；旧 22 页收进「更多」组不删
  // （组名守 ui-copy-standard-v1 宪法#41 + 蓝图词表62——禁词不上屏）。
  var NAV = [
    ["首页", "首页", "/"],
    ["任务", "任务", "/p/mission"],
    ["漏洞", "漏洞", "/p/findings"],
    ["知识库", "知识库", "/p/knowledge"],
    ["收件箱", "收件箱", "/p/inbox"],
    ["设置", "设置", "/p/settings"],
    ["更多", "任务列表", "/p/tasks"],
    ["更多", "新建任务", "/p/new-task"],
    ["更多", "任务回放", "/session"],
    ["更多", "总览", "/console"],
    ["更多", "实时动态", "/console/live"],
    ["更多", "攻击链路", "/console/graph"],
    ["更多", "发现", "/console/findings"],
    ["更多", "播报/介入", "/p/broadcast"],
    ["更多", "复测", "/p/retest"],
    ["更多", "审批中心", "/p/approval-center"],
    ["更多", "拦截审批", "/p/approval"],
    ["更多", "证据", "/evidence"],
    ["更多", "度量与考卷", "/metrics"],
    ["更多", "报告中心", "/p/report-center"],
    ["更多", "能力曲线", "/p/capability"],
    ["更多", "资产库", "/p/asset-registry"],
    ["更多", "测试资产", "/p/assets"],
    ["更多", "资产覆盖", "/p/coverage"],
    ["更多", "技法库", "/p/techniques"],
    ["更多", "实时日志", "/activity"]
  ];
  var entries = NAV.map(function (it) {
    return { id: slugOf(it[2]), group: it[0], label: it[1], href: it[2] };
  });
  var current = (function () {
    if (window.location.pathname === "/") { return ""; }   // 首页=空 id 自认
    var m = window.location.pathname.match(/^\/p\/([a-z0-9-]+)/);
    return m ? m[1] : "";
  })();

  function slugOf(href) {
    var m = String(href).match(/^\/p\/([a-z0-9-]+)/);
    return m ? m[1] : "";
  }
  function esc(s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
  }
  function battleQS() {
    var b = new URLSearchParams(window.location.search).get("battle");
    return b ? "?battle=" + encodeURIComponent(b) : "";
  }

  function push(page) {
    if (!page || !page.id) { return; }
    var label = page.label || page.title || page.id;
    var e = null;
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].id === page.id) { e = entries[i]; break; }
    }
    if (e) {
      e.label = label;
      if (page.group) { e.group = page.group; }
    } else {
      e = { id: page.id, group: page.group || "其他", label: label, href: "/p/" + page.id };
      entries.push(e);
    }
    current = page.id;
    render();
  }

  var CSS = [
    "#glx-btn{position:fixed;left:18px;bottom:18px;z-index:9990;width:46px;height:46px;",
    "border-radius:50%;background:#101216;color:" + ACCENT + ";border:1px solid #3a4049;",
    "font-size:19px;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.5);line-height:1;",
    "font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}",
    "#glx-btn:hover{background:#1d2026}",
    "#glx-veil{position:fixed;inset:0;z-index:9991;background:rgba(10,11,13,.66);display:none}",
    "#glx-veil.on{display:block}",
    "#glx-panel{position:fixed;left:0;top:0;bottom:0;width:250px;z-index:9992;",
    "background:#101216;border-right:1px solid #1d2026;transform:translateX(-100%);",
    "transition:transform .18s ease;display:flex;flex-direction:column;",
    "font:13px/1.5 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#ccd3da}",
    "#glx-panel.on{transform:translateX(0)}",
    "#glx-panel .hd{padding:14px;border-bottom:1px solid #1d2026}",
    "#glx-panel .hd b{color:#e8edf2;font-size:15px;letter-spacing:.5px}",
    "#glx-panel .hd i{display:block;font-style:normal;color:#6b7480;font-size:11px;margin-top:2px}",
    "#glx-panel input{width:100%;box-sizing:border-box;margin-top:10px;background:#16181d;",
    "border:1px solid #2e333b;border-radius:4px;color:#e8edf2;padding:7px 10px;font-size:13px;outline:none}",
    "#glx-panel input:focus{border-color:" + ACCENT + "}",
    "#glx-list{flex:1;overflow-y:auto;padding:6px 0}",
    "#glx-list .grp{padding:9px 14px 3px;color:#6b7480;font-size:11px;letter-spacing:1px}",
    "#glx-list a{display:flex;align-items:center;gap:8px;padding:7px 14px;color:#aab3bd;",
    "text-decoration:none;font-size:13px;border-left:2px solid transparent}",
    "#glx-list a:hover{background:#16181d;color:#e8edf2}",
    "#glx-list a.on{background:#16181d;color:" + ACCENT + ";border-left-color:" + ACCENT + "}",
    "#glx-list a .dot{width:6px;height:6px;border-radius:50%;background:#3a4049;flex-shrink:0}",
    "#glx-list a.on .dot{background:" + ACCENT + "}",
    "#glx-list .none{padding:14px;color:#6b7480;font-size:12px}",
    "#glx-panel .ft{padding:10px 14px;border-top:1px solid #1d2026;font-size:11px;color:#6b7480}"
  ].join("");

  function render() {
    var btn = document.getElementById("glx-btn");
    if (!btn) {
      var st = document.createElement("style");
      st.textContent = CSS;
      document.head.appendChild(st);
      btn = document.createElement("button");
      btn.id = "glx-btn";
      btn.type = "button";
      btn.title = "GraphLed 全站导航（Ctrl+K）";
      btn.textContent = "☰";
      btn.addEventListener("click", function () { toggle(); });
      document.body.appendChild(btn);
    }
    var veil = document.getElementById("glx-veil");
    if (!veil) {
      veil = document.createElement("div");
      veil.id = "glx-veil";
      veil.addEventListener("click", function () { toggle(false); });
      document.body.appendChild(veil);
    }
    var panel = document.getElementById("glx-panel");
    if (!panel) {
      panel = document.createElement("nav");
      panel.id = "glx-panel";
      panel.innerHTML =
        '<div class="hd"><b>GraphLed</b><i>账本为骨 · 图谱为形</i>' +
        '<input id="glx-q" type="text" placeholder="过滤页面…" autocomplete="off"></div>' +
        '<div id="glx-list"></div>' +
        '<div class="ft">Ctrl+K 开合 · Esc 关 · 跳转自动携带当前任务</div>';
      document.body.appendChild(panel);
      panel.addEventListener("click", function (e) {
        if (e.target.tagName === "A") { toggle(false); }
      });
      var q = panel.querySelector("#glx-q");
      q.addEventListener("input", function () { fillList(q.value); });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { toggle(false); }
        if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")
            && !e.shiftKey) {
          e.preventDefault(); cmdk();
          if (panel.classList.contains("on")) { q.focus(); }
        }
      });
    }
    fillList("");
  }

  function fillList(filter) {
    var box = document.getElementById("glx-list");
    if (!box) { return; }
    var kw = (filter || "").trim().toLowerCase();
    var h = "", grp = "";
    entries.forEach(function (e) {
      if (kw && (e.label + e.group + e.id).toLowerCase().indexOf(kw) < 0) { return; }
      if (e.group !== grp) { grp = e.group; h += '<div class="grp">' + esc(grp) + "</div>"; }
      var on = e.id && e.id === current ? " on" : "";
      h += '<a class="' + on.trim() + '" href="' + esc(e.href) + battleQS() + '">' +
        '<span class="dot"></span>' + esc(e.label) + "</a>";
    });
    box.innerHTML = h || '<div class="none">无匹配页面</div>';
  }

  function toggle(force) {
    var panel = document.getElementById("glx-panel");
    var veil = document.getElementById("glx-veil");
    if (!panel || !veil) { return; }
    var on = typeof force === "boolean" ? force : !panel.classList.contains("on");
    panel.classList.toggle("on", on);
    veil.classList.toggle("on", on);
    if (on) {
      var q = document.getElementById("glx-q");
      if (q) { q.value = ""; fillList(""); }
    }
  }

  /* 裸 ⌘K/Ctrl-K 归属（96e10b93 裁）：命令面板在场=让位调 __plkCtl.open()
     （页面清单由面板消费本壳 nav.entries() 单源）；面板缺席=回落本壳抽屉。 */
  function cmdk() {
    var plk = window.__plkCtl;
    if (plk && typeof plk.open === "function") { plk.open(); }
    else { toggle(); }
  }

  try { render(); } catch (e) { /* 壳异常不殃及页面 */ }
  return { push: push, toggle: toggle, cmdk: cmdk,
           entries: function () { return entries.slice(); } };
})();
