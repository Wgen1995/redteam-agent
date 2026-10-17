/* GraphLed 控制台壳（W6）——侧栏 23 页菜单 + 顶栏任务选择器 + Ctrl+K 全局搜索。
   文案律=docs/design/ui-copy-standard-v1.md：导航=名词、界面只说人话；
   未建页显示「建设中·排期W6」占位，不放假数据装真页。 */
"use strict";
var GL = (function () {
  // 导航 23 项：[组, 名称, 路径, "wip"|省略]——空路径=未建页（占位）。
  var NAV = [
    ["任务", "总览", "/console"],
    ["任务", "新建任务", "/new"],
    ["任务", "实时动态", "/console/live"],
    ["任务", "攻击链路", "/console/graph"],
    ["任务", "发现", "/console/findings"],
    ["任务", "任务详情", "/session"],
    ["任务", "对话", "", "wip"],
    ["管控", "审批", "/console/approval"],
    ["管控", "命令记录", "", "wip"],
    ["管控", "证据", "/evidence"],
    ["管控", "通知", "", "wip"],
    ["度量", "基准评测", "/metrics"],
    ["度量", "报告", "", "wip"],
    ["资产", "资产覆盖", "/coverage"],
    ["资产", "工作区", "", "wip"],
    ["系统", "模型池", "", "wip"],
    ["系统", "智能体配置", "", "wip"],
    ["系统", "工具卡", "", "wip"],
    ["系统", "技法库", "", "wip"],
    ["系统", "实时日志", "/activity"],
    ["系统", "设置", "", "wip"],
    ["系统", "用户与角色", "", "wip"],
    ["交付", "验真", "", "wip"]
  ];
  var WIP = "建设中·排期W6";
  var state = { battle: "", navWord: document.body.dataset.nav || "" };

  function qs(key) {
    return new URLSearchParams(window.location.search).get(key) || "";
  }
  function esc(s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
  }
  function fmtNum(n) {
    if (n === null || n === undefined || n === "") return "—";
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  function withBattle(path) {
    return state.battle ? path + (path.indexOf("?") >= 0 ? "&" : "?") + "battle=" + encodeURIComponent(state.battle) : path;
  }
  function api(path) {
    return fetch(withBattle(path), { credentials: "same-origin" })
      .then(function (r) {
        if (r.status === 401) { window.location.href = "/login"; throw new Error("未登录"); }
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
  }
  function postJSON(path, body) {
    return fetch(withBattle(path), {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
      body: JSON.stringify(body)
    }).then(function (r) { return r.json().then(function (j) { return { status: r.status, json: j }; }); });
  }
  function notice(msg) {
    var n = document.getElementById("ntc");
    if (!n) return;
    n.textContent = msg;
    n.style.display = "block";
    clearTimeout(n._t);
    n._t = setTimeout(function () { n.style.display = "none"; }, 2400);
  }
  function drawer(html) {
    var d = document.getElementById("drawer");
    if (!d) return;
    if (html !== undefined) document.getElementById("drawer-body").innerHTML = html;
    d.classList.toggle("on", html !== false);
  }

  // ---- 壳渲染 ----
  function renderSide() {
    var side = document.getElementById("side");
    if (!side) return;
    var h = '<div class="logo"><b>GraphLed</b><i>记录为骨 · 图谱为形</i></div><nav id="nav">';
    var grp = "";
    NAV.forEach(function (it) {
      if (it[0] !== grp) { grp = it[0]; h += '<div class="grp">' + esc(grp) + "</div>"; }
      var live = !!it[2];
      var on = state.navWord && it[1] === state.navWord ? " on" : "";
      h += '<div class="nav-item' + on + '" data-href="' + esc(it[2]) + '" data-wip="' + (live ? "" : "1") + '">' +
        '<span class="dot"></span>' + esc(it[1]) +
        (live ? "" : '<span class="wip">' + WIP.slice(0, 3) + "</span>") + "</div>";
    });
    h += '</nav><div class="foot">本页数据全部来自任务记录<br>只能看不能改 · v1.0</div>';
    side.innerHTML = h;
    side.addEventListener("click", function (e) {
      var el = e.target.closest(".nav-item");
      if (!el) return;
      if (el.dataset.wip === "1") { notice("「" + el.textContent.trim().replace(WIP.slice(0, 3), "") + "」" + WIP); return; }
      window.location.href = el.dataset.href + (state.battle ? "?battle=" + encodeURIComponent(state.battle) : "");
    });
  }
  function renderTop(battles) {
    var top = document.getElementById("top");
    if (!top) return;
    var opts = (battles || []).map(function (b) {
      var label = b.id + (b.target ? " · " + b.target : "");
      return '<option value="' + b.n + '"' + (String(b.n) === String(state.battle || currentN(battles)) ? " selected" : "") + ">" + esc(label) + "</option>";
    }).join("");
    top.innerHTML =
      '<select id="battle-select" class="sel" title="切换任务">' + opts + "</select>" +
      '<span class="sp"></span>' +
      '<span class="kbd">Ctrl</span><span class="kbd">K</span><span style="color:var(--g8);font-size:11px">全局搜索</span>' +
      '<span class="sp"></span>' +
      '<div class="who">操作员 · <b>已登录</b></div>';
    top.addEventListener("change", function (e) {
      if (e.target.id !== "battle-select") return;
      var v = e.target.value;
      var base = window.location.pathname;
      window.location.href = v ? base + "?battle=" + encodeURIComponent(v) : base;
    });
  }
  function currentN(battles) {
    return battles && battles.length ? battles[battles.length - 1].n : "";
  }
  function renderCmdk() {
    var box = document.createElement("div");
    box.id = "cmdk";
    box.innerHTML = '<div class="box"><input id="cmdk-input" placeholder="搜索页面…（Ctrl+K）"><div id="cmdk-results"></div></div>';
    document.body.appendChild(box);
    var input = box.querySelector("#cmdk-input"), out = box.querySelector("#cmdk-results");
    function go(item) {
      box.classList.remove("on");
      if (!item[2]) { notice("「" + item[1] + "」" + WIP); return; }
      window.location.href = item[2] + (state.battle ? "?battle=" + encodeURIComponent(state.battle) : "");
    }
    function render(q) {
      var hits = NAV.filter(function (it) { return !q || it[1].indexOf(q) >= 0; }).slice(0, 8);
      out.innerHTML = hits.map(function (it, i) {
        return '<div class="r' + (i === 0 ? " on" : "") + '" data-i="' + NAV.indexOf(it) + '">' +
          esc(it[1]) + '<span style="color:var(--g8);font-size:11px">' +
          (it[2] ? " → " + esc(it[2]) : " · " + WIP) + "</span></div>";
      }).join("");
    }
    input.addEventListener("input", function () { render(input.value.trim()); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { var first = out.querySelector(".r"); if (first) go(NAV[+first.dataset.i]); }
    });
    out.addEventListener("click", function (e) {
      var el = e.target.closest(".r");
      if (el) go(NAV[+el.dataset.i]);
    });
    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        box.classList.add("on");
        input.focus();
        render("");
      } else if (e.key === "Escape") { box.classList.remove("on"); drawer(false); }
    });
  }
  function renderChromeExtras() {
    var n = document.createElement("div");
    n.className = "notice"; n.id = "ntc";
    document.body.appendChild(n);
    var d = document.createElement("div");
    d.className = "detail"; d.id = "drawer";
    d.innerHTML = '<span class="x" data-close>✕</span><div id="drawer-body"></div>';
    document.body.appendChild(d);
    d.addEventListener("click", function (e) { if (e.target.dataset && e.target.dataset.close !== undefined) drawer(false); });
  }

  function boot(pageApi, init) {
    state.battle = qs("battle");
    renderSide();
    renderCmdk();
    renderChromeExtras();
    api(pageApi).then(function (data) {
      renderTop(data && data.battles);
      init(data);
    }).catch(function (e) {
      var v = document.getElementById("view");
      if (v) v.insertAdjacentHTML("afterbegin", '<div class="pane"><div class="empty">数据载入失败：' + esc(String(e.message || e)) + "</div></div>");
    });
  }
  return { NAV: NAV, WIP: WIP, qs: qs, esc: esc, fmtNum: fmtNum, api: api, withBattle: withBattle,
           postJSON: postJSON, notice: notice, drawer: drawer, boot: boot };
})();
