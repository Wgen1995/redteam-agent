/* -*- coding: utf-8 -*- ⌘K/Ctrl-K 全局命令面板（可挂载组件·冒烟舰施工）
 * ============================================================================
 * 契约（与总装舰/UI-1 协调——本文件=命令面板组件单源，壳层注入由总装舰收口）：
 *   · 本组件零框架零 CDN（宪法：前端零框架零 CDN），纯 vanilla，挂到任意已挂
 *     页即可用；页面只加一小段守卫式加载器（见 techniques.html 冒烟挂载），
 *     或由总装舰壳统一注入一次——届时各页加载器可退役。
 *   · 页面清单单源=壳侧：mount() 优先消费总装壳 window.nav.entries()
 *     （/static/app.js 导航网——{id,label,group,href} 同形）；壳缺席时退回
 *     内置 DEFAULT_PAGES（镜像 nav.push 自注册+既有观察面页）。壳侧还可用
 *     window.__PALETTE_PAGES__ 同形数组注入（同 id 壳侧胜）。
 *   · ⌘K 键位协调（总装壳 app.js 已绑 Ctrl/⌘+K 开导航抽屉）：壳在场时本面板
 *     让位裸 ⌘K（不 preventDefault——壳抽屉照常开合），自身绑 ⌘⇧K/Ctrl-Shift-K；
 *     壳缺席时本面板独占裸 ⌘K。总装舰愿交出 ⌘K 时：壳侧删其键位或改调
 *     window.__plkCtl.open() 即可，本组件零改动。
 *   · 资产路由待总装舰收口：server.py 现只放行 /static/app.js——本组件需一条
 *     /static/pages/*.js 放行（或壳统一注入）才能在生产页加载；加载器候选见
 *     techniques.html（缺席=守卫静默，不破页）。
 *   · 纯逻辑函数（索引/匹配/分组/行址解析/最近使用）全部可 require——
 *     tests/test_webui_palette.py 用 node 直跑（无 DOM 也加载成功）。
 *   · 文案宪法#41（界面人话律）：「任务」不说「战」，内部代号不上屏；
 *     FD-/G-/EV- 是账本行址（各页 mono 展示的产品标识），不是内部代号。
 * ============================================================================
 */
(function (root, factory) {
  var api = factory(root);
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
  root.Palette = api;
})(typeof self !== "undefined" ? self : globalThis, function (root) {
  "use strict";

  /* ================= 常量（单源） ================= */

  var RECENT_KEY = "tanyin.palette.recent.v1";   /* localStorage 键 */
  var RECENT_CAP = 8;                             /* 最近使用上限 */
  var GROUP_RECENT = "最近使用", GROUP_ADDR = "查找",
      GROUP_ACTION = "动作", GROUP_PAGE = "页面";
  var GROUP_ORDER = [GROUP_RECENT, GROUP_ADDR, GROUP_ACTION, GROUP_PAGE];

  /* 默认页面清单（壳缺席时的退回面）：
   *   · 新页 file=兄弟页相对名（/p/<slug> 路由下相对解析为 /p/<slug>.html——
   *     api_pages「兄弟页相对链接形」同律，tasks.html NEW_TASK_URL 先例）；
   *   · 既有观察面/控制台页 href=绝对路由（app.js 导航网同源镜像）。
   * 壳在场时 mount() 用 nav.entries() 覆盖（同 id 壳侧胜）。 */
  var DEFAULT_PAGES = [
    { id: "console",         href: "/console",             title: "总览",     group: "作战" },
    { id: "tasks",           file: "tasks.html",           title: "任务列表", group: "作战" },
    { id: "new-task",        file: "new-task.html",        title: "新建任务", group: "作战" },
    { id: "session",         href: "/session",             title: "任务详情", group: "作战" },
    { id: "live",            href: "/console/live",        title: "实时动态", group: "作战" },
    { id: "graph",           href: "/console/graph",       title: "攻击链路", group: "作战" },
    { id: "console-findings", href: "/console/findings",   title: "发现",     group: "作战" },
    { id: "broadcast",       file: "broadcast.html",       title: "播报",     group: "作战" },
    { id: "retest",          file: "retest.html",          title: "复测",     group: "作战" },
    { id: "approval-center", file: "approval-center.html", title: "审批中心", group: "管控" },
    { id: "approval",        file: "approval.html",        title: "拦截审批", group: "管控" },
    { id: "evidence",        href: "/evidence",            title: "证据",     group: "管控" },
    { id: "metrics",         href: "/metrics",             title: "度量与考卷", group: "度量" },
    { id: "report-center",   file: "report-center.html",   title: "报告中心", group: "度量" },
    { id: "asset-registry",  file: "asset-registry.html",  title: "资产库",   group: "资产" },
    { id: "assets",          file: "assets.html",          title: "测试资产", group: "资产" },
    { id: "coverage",        file: "coverage.html",        title: "资产覆盖", group: "资产" },
    { id: "techniques",      file: "techniques.html",      title: "技法库",   group: "系统" },
    { id: "activity",        href: "/activity",            title: "实时日志", group: "系统" },
    { id: "settings",        file: "settings.html",        title: "设置",     group: "系统" },
    { id: "finding-detail",  file: "finding-detail.html",  title: "漏洞详情", group: "发现" },
    { id: "tools",           file: "tools.html",           title: "工具",     group: "系统" },
    { id: "llm-status",      file: "llm-status.html",      title: "模型状态", group: "系统" },
    { id: "evals",           file: "evals.html",           title: "评测对比", group: "系统" },
    { id: "workspace",       file: "workspace.html",       title: "工作区",   group: "系统" }
  ];

  /* 高频动作（人话律#41：任务不说战；hint 给用途不打代号） */
  var ACTIONS = [
    { id: "act:new-task",       kind: "action", title: "新建任务",
      hint: "填写表单创建", keys: "new create 新建 创建 任务",
      url: "new-task.html" },
    { id: "act:latest-battle",  kind: "action", title: "打开最新任务",
      hint: "按最近更新定位任务详情", keys: "latest battle 最新 任务 任务详情",
      act: "latest-battle" },
    { id: "act:latest-finding", kind: "action", title: "跳到最新发现",
      hint: "最新任务的发现列表", keys: "latest finding 最新 发现 漏洞",
      act: "latest-finding" },
    { id: "act:open-report",    kind: "action", title: "打开报告中心",
      hint: "报告渲染与签发", keys: "report 报告 签发 渲染",
      url: "report-center.html" }
  ];

  var ADDR_RE = /^(FD|EV|G)-([A-Za-z0-9_.-]+)(?:@(G-[A-Za-z0-9_.-]+))?\s*$/i;

  /* ================= 纯逻辑（node 直跑，零 DOM） ================= */

  /* 模糊打分：子串 > 连续/词首子序列；不匹配=null。确定性（无墙钟无随机）。
   *  - 命中子串：1000 - 位置*2 - 长度差（越前越短越好）
   *  - 子序列：逐字累 10 + 连击奖励 + 词首奖励 - 跳距罚 - 目标长度微罚
   *  - CJK 每字自成词首（「任」对「任务列表」拿词首分——与拉丁词首同律） */
  function isWordStart(t, i) {
    if (i <= 0) { return true; }
    var prev = t.charAt(i - 1);
    return !/[a-z0-9]/.test(prev);
  }
  function fuzzyScore(query, target) {
    var q = String(query == null ? "" : query).toLowerCase();
    var t = String(target == null ? "" : target).toLowerCase();
    if (!q) { return 0; }
    if (!t) { return null; }
    var at = t.indexOf(q);
    if (at >= 0) { return 1000 - at * 2 - (t.length - q.length); }
    var score = 0, ti = 0, streak = 0;
    for (var k = 0; k < q.length; k++) {
      var ch = q.charAt(k);
      var idx = t.indexOf(ch, ti);
      if (idx < 0) { return null; }
      streak = (idx === ti && k > 0) ? streak + 1 : 0;
      score += 10 + (streak > 0 ? 6 * streak : 0)
                  + (isWordStart(t, idx) ? 8 : 0)
                  - Math.min(idx - ti, 5);
      ti = idx + 1;
    }
    return score - t.length;
  }

  /* 行址解析：FD-xxx / EV-xxx / G-xxx（可 @G-yy 带所属任务代域）。
   * 大小写不敏感；普通关键词=null。 */
  function parseAddress(query) {
    var q = String(query == null ? "" : query).trim();
    if (!q) { return null; }
    var m = ADDR_RE.exec(q);
    if (!m) { return null; }
    return { kind: String(m[1]).toUpperCase(),
             id: m[1].toUpperCase() + "-" + m[2], goal: m[3] || "" };
  }

  /* 页面清单合并：壳侧（同 id）胜，保默认序中未覆盖项（追加在尾）。
   * 壳形 {id,label,group,href}（nav.entries）/ 内建形 {id,title,group,file|href}
   * 都收；href=绝对路由优先，file=兄弟页相对名。 */
  function mergePages(base, extra) {
    var out = base.map(function (p) { return {
      id: p.id, title: p.title || "", group: p.group || "",
      file: p.file || "", href: p.href || "" }; });
    var byId = {};
    out.forEach(function (p) { byId[p.id] = true; });
    (extra || []).forEach(function (p) {
      if (!p || !p.id) { return; }
      var title = p.title || p.label || "";
      var href = p.href || "";
      var file = p.file || "";
      if (byId[p.id]) {
        out = out.map(function (b) {
          if (b.id !== p.id) { return b; }
          var m = { id: b.id, title: title || b.title,
                    group: p.group || b.group,
                    file: file || (href ? "" : b.file), href: href || b.href };
          if (!m.file && !m.href) { m.file = b.file || (b.id + ".html"); }
          return m;
        });
      } else if (title && (href || file)) {
        out.push({ id: p.id, title: title, group: p.group || "其他",
                   file: file, href: href });
      }
    });
    return out;
  }

  /* 页面 → 跳转 URL（href 绝对路由优先；否则兄弟页相对名）。 */
  function pageUrl(p) {
    if (!p) { return ""; }
    return p.href || p.file || (p.id + ".html");
  }

  /* 命令索引：动作在前（高频），页面在后（导航全量）。 */
  function buildCommands(pages) {
    var cmds = ACTIONS.map(function (a) {
      return { id: a.id, kind: "action", title: a.title, group: GROUP_ACTION,
               hint: a.hint || "", keys: a.keys || "",
               url: a.url || null, act: a.act || null };
    });
    (pages || []).forEach(function (p) {
      cmds.push({ id: "page:" + p.id, kind: "page", title: p.title,
                  group: GROUP_PAGE, hint: p.group || "",
                  keys: [p.title, p.group, p.id].join(" "),
                  url: pageUrl(p) });
    });
    return cmds;
  }

  /* 行址 → 查找命令（纯构造：跳转目标由 run 期解析）。 */
  function addrCommand(addr) {
    if (!addr) { return null; }
    if (addr.kind === "FD") {
      return { id: "addr:fd:" + addr.id + ":" + addr.goal, kind: "addr",
               title: "直达发现 " + addr.id,
               hint: addr.goal ? "所属任务 " + addr.goal : "可补 @G-代域 定所属任务",
               mono: addr.id, url: findingUrl(addr.id, addr.goal) };
    }
    if (addr.kind === "EV") {
      return { id: "addr:ev:" + addr.id + ":" + addr.goal, kind: "addr",
               title: "直达证据 " + addr.id,
               hint: addr.goal ? "所属任务 " + addr.goal + " · 转挂接发现"
                               : "查各任务播报 · 转挂接发现",
               mono: addr.id, act: "ev:" + addr.id + (addr.goal ? "@" + addr.goal : "") };
    }
    if (addr.kind === "G") {
      return { id: "addr:g:" + addr.id, kind: "addr",
               title: "直达任务 " + addr.id,
               hint: "按代域定位任务详情", mono: addr.id,
               act: "goal:" + addr.id };
    }
    return null;
  }

  /* 匹配：标题/关键词取高分；行址查询时查找命令置顶。空查询=全量基序。 */
  function matchCommands(query, commands) {
    var q = String(query == null ? "" : query).trim();
    var out = [];
    if (!q) {
      (commands || []).forEach(function (c, i) { out.push({ cmd: c, score: 0, i: i }); });
      return out;
    }
    var addr = parseAddress(q);
    (commands || []).forEach(function (c, i) {
      var s = fuzzyScore(q, c.title);
      var sk = fuzzyScore(q, (c.keys || "") + " " + (c.mono || ""));
      if (sk != null) { sk -= 2; }
      var best = (s == null) ? sk : (sk == null ? s : Math.max(s, sk));
      if (best != null) { out.push({ cmd: c, score: best, i: i }); }
    });
    out.sort(function (a, b) { return (b.score - a.score) || (a.i - b.i); });
    if (addr) {
      var ac = addrCommand(addr);
      if (ac) { out.unshift({ cmd: ac, score: 2000, i: -1 }); }
    }
    return out;
  }

  /* 分组：固定序（最近使用 → 查找 → 动作 → 页面），组内保匹配序；
   * 最近使用按 recents 序取交集（空=不出现该组）。 */
  function groupCommands(matched, recentIds) {
    var byId = {};
    (matched || []).forEach(function (m) { byId[m.cmd.id] = m.cmd; });
    var groups = {};
    groups[GROUP_RECENT] = [];
    (recentIds || []).forEach(function (rid) {
      var c = byId[rid];
      if (c && (c.kind === "page" || c.kind === "action")) {
        groups[GROUP_RECENT].push(c);
      }
    });
    [GROUP_ADDR, GROUP_ACTION, GROUP_PAGE].forEach(function (g) { groups[g] = []; });
    (matched || []).forEach(function (m) {
      var c = m.cmd;
      var g = c.kind === "addr" ? GROUP_ADDR
            : c.kind === "action" ? GROUP_ACTION
            : c.kind === "page" ? GROUP_PAGE : null;
      if (!g) { return; }
      if (groups[GROUP_RECENT].indexOf(c) >= 0) { return; }   /* 已在最近使用不重复 */
      groups[g].push(c);
    });
    var out = [];
    GROUP_ORDER.forEach(function (g) {
      if (groups[g] && groups[g].length) { out.push({ label: g, items: groups[g] }); }
    });
    return out;
  }

  /* 分组扁平化（键盘选择的线性序）。 */
  function flattenGroups(groups) {
    var flat = [];
    (groups || []).forEach(function (g) {
      (g.items || []).forEach(function (c) { flat.push(c); });
    });
    return flat;
  }

  /* 最近使用：置顶去重 + 截断（纯函数——不碰 storage）。 */
  function pushRecent(list, id, cap) {
    var c = cap == null ? RECENT_CAP : cap;
    var out = [id].concat((list || []).filter(function (x) { return x !== id; }));
    return out.slice(0, c);
  }

  /* 最新任务：updated（ISO-Z 字典序可比较）最大者；平手取任务号大者。 */
  function latestBattle(battles) {
    var best = null;
    (battles || []).forEach(function (b) {
      if (!best) { best = b; return; }
      var bu = String(b.updated || ""), ku = String(best.updated || "");
      if (bu > ku || (bu === ku && Number(b.n || 0) > Number(best.n || 0))) { best = b; }
    });
    return best;
  }

  /* G- 代域 → 任务：最新代域名 / goals 行 id / 任务号（battle-N、纯数字）
   * 精确命中（大小写不敏感）；≥3 字符前缀兜底；无=null。 */
  function resolveGoalAddr(battles, addr) {
    var a = String(addr == null ? "" : addr).trim().toLowerCase();
    if (!a) { return null; }
    var digits = a.replace(/^battle-/, "");
    var pick = null;
    (battles || []).forEach(function (b) {
      var goal = String(b.goal || "").toLowerCase();
      var gid = String(b.goal_id || "").toLowerCase();
      var bid = String(b.battle || "").toLowerCase();
      if (goal === a || gid === a || bid === a
          || (/^\d+$/.test(digits) && String(b.n) === digits)) {
        if (!pick) { pick = b; }
      }
    });
    if (pick) { return pick; }
    if (a.length >= 3) {
      (battles || []).forEach(function (b) {
        var goal = String(b.goal || "").toLowerCase();
        if (!pick && goal && goal.indexOf(a) === 0) { pick = b; }
      });
    }
    return pick || null;
  }

  /* 播报行证据表 → 挂接发现（broadcast.json rows[].evidence[] 单源）。 */
  function evTarget(rows, evId) {
    var hit = null;
    (rows || []).forEach(function (r) {
      if (hit) { return; }
      ((r && r.evidence) || []).forEach(function (e) {
        if (!hit && e && e.id === evId && e.finding) { hit = { finding: e.finding }; }
      });
    });
    return hit;
  }

  /* URL 构造（纯；encode 交给调用侧的值已由行址正则限定安全字符） */
  function findingUrl(id, goal) {
    return "finding-detail.html?id=" + encodeURIComponent(id)
         + (goal ? "&goal=" + encodeURIComponent(goal) : "");
  }
  function sessionUrl(n) { return "/session?battle=" + encodeURIComponent(n); }
  function findingsUrl(n) { return "/console/findings?battle=" + encodeURIComponent(n); }

  var pure = {
    RECENT_KEY: RECENT_KEY, RECENT_CAP: RECENT_CAP,
    GROUP_ORDER: GROUP_ORDER, DEFAULT_PAGES: DEFAULT_PAGES,
    fuzzyScore: fuzzyScore, parseAddress: parseAddress,
    mergePages: mergePages, buildCommands: buildCommands,
    addrCommand: addrCommand, matchCommands: matchCommands,
    groupCommands: groupCommands, flattenGroups: flattenGroups,
    pushRecent: pushRecent, latestBattle: latestBattle,
    resolveGoalAddr: resolveGoalAddr, evTarget: evTarget,
    findingUrl: findingUrl, sessionUrl: sessionUrl, findingsUrl: findingsUrl,
    pageUrl: pageUrl
  };

  /* ================= 挂载（DOM；Node 下 mount() 安静返回 null） ================= */

  function mount(opts) {
    if (typeof document === "undefined") { return null; }
    if (root.__plkCtl) { return root.__plkCtl; }
    opts = opts || {};

    /* 页面清单：壳导航网（nav.entries 单源）优先，__PALETTE_PAGES__/opts.pages
     * 追加注入（同 id 壳侧胜），全缺席退回内置 DEFAULT_PAGES。 */
    var shellPages = [];
    try {
      if (root.nav && typeof root.nav.entries === "function") {
        shellPages = root.nav.entries() || [];
      }
    } catch (e) { shellPages = []; }
    var extraPages = (opts.pages || root.__PALETTE_PAGES__ || []);
    var pages = mergePages(DEFAULT_PAGES, shellPages.concat(extraPages));
    var shellPresent = !!(root.nav && typeof root.nav.toggle === "function");
    var commands = buildCommands(pages);
    var navigate = opts.navigate || function (url) { root.location.href = url; };
    var fetchJSON = opts.fetchImpl
      || function (url) {
          return fetch(url, { credentials: "same-origin" }).then(function (r) {
            if (r.status === 401) { root.location.href = "/login";
                                    throw new Error("须登录"); }
            if (!r.ok) { throw new Error("HTTP " + r.status); }
            return r.json();
          });
        };
    var recentKey = opts.storageKey || RECENT_KEY;

    /* —— DOM 装配 —— */
    var css = document.createElement("style");
    css.id = "plk-style";
    css.textContent = [
      ".plk-root{position:fixed;inset:0;z-index:2147483000;display:none;",
      "align-items:flex-start;justify-content:center;",
      "background:rgba(6,8,10,.62);backdrop-filter:blur(6px) saturate(.9)}",
      ".plk-root.on{display:flex}",
      ".plk-panel{width:min(680px,94vw);margin-top:16vh;max-height:min(64vh,560px);",
      "display:flex;flex-direction:column;overflow:hidden;border-radius:10px;",
      "background:var(--g1,#101216);border:1px solid var(--g4,#252930);",
      "box-shadow:0 24px 72px rgba(0,0,0,.55),0 2px 8px rgba(0,0,0,.4);",
      "animation:plk-in .13s ease-out}",
      "@keyframes plk-in{from{opacity:0;transform:translateY(-8px) scale(.985)}",
      "to{opacity:1;transform:none}}",
      ".plk-head{display:flex;align-items:center;gap:10px;padding:13px 16px;",
      "border-bottom:1px solid var(--g3,#1d2026)}",
      ".plk-glyph{color:var(--g7,#4c535e);font-family:var(--mono,Menlo,monospace);",
      "font-size:13px}",
      ".plk-input{flex:1;background:none;border:none;outline:none;",
      "color:var(--gc,#e8edf2);font:15px/1.4 -apple-system,'PingFang SC',",
      "'Microsoft YaHei',sans-serif}",
      ".plk-input::placeholder{color:var(--g8,#6b7480)}",
      ".plk-list{overflow:auto;flex:1;padding:6px 0 8px}",
      ".plk-list::-webkit-scrollbar{width:6px}",
      ".plk-list::-webkit-scrollbar-thumb{background:var(--g4,#252930);border-radius:3px}",
      ".plk-g{padding:9px 16px 3px;color:var(--g8,#6b7480);font-size:11px;",
      "letter-spacing:.6px}",
      ".plk-item{display:flex;align-items:center;gap:10px;padding:7px 16px;",
      "cursor:pointer;border-left:2px solid transparent}",
      ".plk-item .t{color:var(--gb,#ccd3da);font-size:13px;white-space:nowrap;",
      "overflow:hidden;text-overflow:ellipsis}",
      ".plk-item .mono{font-family:var(--mono,Menlo,monospace);font-size:12px;",
      "color:var(--ga,#aab3bd)}",
      ".plk-item .hint{margin-left:auto;color:var(--g8,#6b7480);font-size:11.5px;",
      "white-space:nowrap}",
      ".plk-item.sel{background:var(--g2,#16181d);border-left-color:var(--acc,#3ddc97)}",
      ".plk-item.sel .t{color:var(--gc,#e8edf2)}",
      ".plk-empty{padding:26px 16px;text-align:center;color:var(--g8,#6b7480);",
      "font-size:12.5px;line-height:1.8}",
      ".plk-foot{display:flex;align-items:center;gap:12px;padding:8px 16px;",
      "border-top:1px solid var(--g3,#1d2026);background:var(--g1,#0d0f12);",
      "color:var(--g8,#6b7480);font-size:11px}",
      ".plk-foot kbd{font-family:var(--mono,Menlo,monospace);font-size:10px;",
      "color:var(--g9,#8b949f);border:1px solid var(--g5,#2e333b);border-radius:3px;",
      "padding:1px 5px;background:var(--g2,#16181d)}",
      ".plk-foot .sp{flex:1}",
      ".plk-foot .msg{font-size:11.5px}",
      ".plk-foot .msg.busy{color:var(--info,#5aa9e6)}",
      ".plk-foot .msg.err{color:var(--dang,#e8635a)}"
    ].join("");
    document.head.appendChild(css);

    var ov = document.createElement("div");
    ov.className = "plk-root";
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    ov.setAttribute("aria-label", "命令面板");
    ov.innerHTML =
      '<div class="plk-panel">' +
        '<div class="plk-head"><span class="plk-glyph">&gt;_</span>' +
          '<input class="plk-input" aria-label="搜索页面、动作或行址" ' +
          'placeholder="搜索页面、动作，或输入行址直达（FD- 发现 / G- 任务 / EV- 证据）" ' +
          'autocomplete="off" spellcheck="false"></div>' +
        '<div class="plk-list"></div>' +
        '<div class="plk-foot"><kbd>↑↓</kbd> 选择 <kbd>回车</kbd> 打开 ' +
          '<kbd>esc</kbd> 关闭 <kbd>' + (shellPresent ? "⌘⇧K" : "⌘K") + "</kbd> 呼出" +
          '<span class="sp"></span><span class="plk-msg msg"></span>' +
          '<span class="plk-count"></span></div>' +
      "</div>";
    document.body.appendChild(ov);

    var input = ov.querySelector(".plk-input");
    var listEl = ov.querySelector(".plk-list");
    var msgEl = ov.querySelector(".plk-msg");
    var countEl = ov.querySelector(".plk-count");

    var open_ = false, sel = 0, flat = [], lastFocus = null;

    function readRecents() {
      try {
        var raw = root.localStorage.getItem(recentKey);
        var v = JSON.parse(raw || "[]");
        return Array.isArray(v) ? v.filter(function (x) { return typeof x === "string"; }) : [];
      } catch (e) { return []; }
    }
    function writeRecents(list) {
      try { root.localStorage.setItem(recentKey, JSON.stringify(list)); } catch (e) {}
    }
    function setMsg(text, cls) {
      msgEl.textContent = text || "";
      msgEl.className = "plk-msg msg" + (cls ? " " + cls : "");
    }
    function esc(s) {
      return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }

    function render() {
      var q = input.value;
      var matched = matchCommands(q, commands);
      var groups = groupCommands(matched, readRecents());
      flat = flattenGroups(groups);
      if (sel >= flat.length) { sel = Math.max(0, flat.length - 1); }
      if (!flat.length) {
        listEl.innerHTML = '<div class="plk-empty">没有匹配的命令。<br>' +
          "试试页面名称、动作关键词，或输入行址（FD- 发现 / G- 任务 / EV- 证据）。</div>";
        countEl.textContent = "";
        return;
      }
      var html = "";
      groups.forEach(function (g) {
        html += '<div class="plk-g">' + esc(g.label) + "</div>";
        g.items.forEach(function (c) {
          var i = flat.indexOf(c);
          html += '<div class="plk-item' + (i === sel ? " sel" : "") +
            '" data-i="' + i + '" role="option" aria-selected="' + (i === sel) + '">' +
            '<span class="t">' + esc(c.title) + "</span>" +
            (c.mono ? '<span class="mono">' + esc(c.mono) + "</span>" : "") +
            (c.hint ? '<span class="hint">' + esc(c.hint) + "</span>" : "") +
            "</div>";
        });
      });
      listEl.innerHTML = html;
      countEl.textContent = flat.length + " 项";
      var selEl = listEl.querySelector('.plk-item.sel');
      if (selEl && selEl.scrollIntoView) {
        selEl.scrollIntoView({ block: "nearest" });
      }
    }

    function open() {
      if (open_) { return; }
      open_ = true;
      lastFocus = document.activeElement;
      input.value = "";
      sel = 0;
      setMsg("");
      ov.classList.add("on");
      render();
      input.focus();
      input.select();
    }
    function close() {
      if (!open_) { return; }
      open_ = false;
      ov.classList.remove("on");
      if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (e) {} }
    }
    function toggle() { open_ ? close() : open(); }
    function move(d) {
      if (!flat.length) { return; }
      sel = (sel + d + flat.length) % flat.length;
      render();
    }

    function record(cmd) {
      writeRecents(pushRecent(readRecents(), cmd.id));
    }

    /* 行址/动作的异步解析：busy → 成功跳转 / 失败人话（宪法#41）且面板留开 */
    function runAct(cmd) {
      var act = cmd.act || "";
      if (act === "latest-battle" || act === "latest-finding") {
        setMsg("载入任务清单…", "busy");
        return fetchJSON("/api/v2/tasks.json").then(function (p) {
          var b = latestBattle((p && p.battles) || []);
          if (!b) { setMsg("暂无任务——先新建一个任务", "err"); return; }
          record(cmd);
          navigate(act === "latest-battle" ? sessionUrl(b.n) : findingsUrl(b.n));
        }, function (e) { setMsg("数据载入失败：" + e.message, "err"); });
      }
      if (act.indexOf("goal:") === 0) {
        var gaddr = act.slice(5);
        setMsg("定位任务 " + gaddr + " …", "busy");
        return fetchJSON("/api/v2/tasks.json").then(function (p) {
          var b = resolveGoalAddr((p && p.battles) || [], gaddr);
          if (!b) { setMsg("未找到任务 " + gaddr + "——可在任务列表核对代域", "err"); return; }
          record(cmd);
          navigate(sessionUrl(b.n));
        }, function (e) { setMsg("数据载入失败：" + e.message, "err"); });
      }
      if (act.indexOf("ev:") === 0) {
        var rest = act.slice(3);
        var at = rest.indexOf("@");
        var evid = at >= 0 ? rest.slice(0, at) : rest;
        var egoal = at >= 0 ? rest.slice(at + 1) : "";
        setMsg("查证据 " + evid + " 挂接的发现…", "busy");
        return fetchJSON("/api/v2/tasks.json").then(function (p) {
          var battles = (p && p.battles) || [];
          var ordered = battles.slice();
          if (egoal) {
            var b = resolveGoalAddr(battles, egoal);
            if (!b) {
              setMsg("未找到任务 " + egoal + "——可在任务列表核对代域", "err");
              return Promise.resolve(null);
            }
            ordered = [b];
          }
          var tryNext = function (i) {
            if (i >= Math.min(ordered.length, 8)) {
              setMsg("未找到证据 " + evid + " 挂接的发现（逐任务查最近 8 个任务）", "err");
              return Promise.resolve(null);
            }
            var bb = ordered[i];
            return fetchJSON("/api/v2/broadcast.json?battle=" + encodeURIComponent(bb.n) +
                             "&tail=5000").then(function (bp) {
              var hit = evTarget((bp && bp.rows) || [], evid);
              if (hit) { return { b: bb, hit: hit }; }
              return tryNext(i + 1);
            }, function () { return tryNext(i + 1); });
          };
          return tryNext(0).then(function (r) {
            if (!r) { return; }
            record(cmd);
            navigate(findingUrl(r.hit.finding, r.b.goal));
          });
        }, function (e) { setMsg("数据载入失败：" + e.message, "err"); });
      }
      return Promise.resolve();
    }

    function run(cmd) {
      if (!cmd) { return; }
      if (cmd.url) {
        record(cmd);
        setMsg("");
        navigate(cmd.url);
        return;
      }
      if (cmd.act) { runAct(cmd); }
    }

    /* —— 事件（capture 优先于页内处理器） ——
     * 键位协调：总装壳在场（nav.toggle 绑了裸 ⌘K 开导航抽屉）时，裸 ⌘K 让位
     * （不拦——壳抽屉照常），本面板绑 ⌘⇧K / Ctrl-Shift-K；壳缺席时独占裸 ⌘K。 */
    document.addEventListener("keydown", function (e) {
      if (e.isComposing) { return; }
      if ((e.metaKey || e.ctrlKey) && !e.altKey && e.code === "KeyK") {
        if (e.shiftKey) {
          e.preventDefault();
          e.stopPropagation();
          toggle();
          return;
        }
        if (shellPresent) { return; }   /* 让位壳抽屉（协调点，见文件头） */
        e.preventDefault();
        e.stopPropagation();
        toggle();
        return;
      }
      if (!open_) { return; }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault(); e.stopPropagation();
        move(e.key === "ArrowDown" ? 1 : -1);
      } else if (e.key === "Enter") {
        e.preventDefault(); e.stopPropagation();
        run(flat[sel]);
      } else if (e.key === "Escape") {
        e.preventDefault(); e.stopPropagation();
        close();
      }
    }, true);

    input.addEventListener("input", function () { sel = 0; setMsg(""); render(); });
    listEl.addEventListener("mousemove", function (e) {
      var row = e.target && e.target.closest ? e.target.closest(".plk-item") : null;
      if (!row) { return; }
      var i = Number(row.getAttribute("data-i"));
      if (!isNaN(i) && i !== sel) { sel = i; render(); }
    });
    listEl.addEventListener("click", function (e) {
      var row = e.target && e.target.closest ? e.target.closest(".plk-item") : null;
      if (!row) { return; }
      var i = Number(row.getAttribute("data-i"));
      if (!isNaN(i)) { sel = i; run(flat[i]); }
    });
    ov.addEventListener("mousedown", function (e) { if (e.target === ov) { close(); } });

    var ctl = { open: open, close: close, toggle: toggle,
                isOpen: function () { return open_; },
                refresh: render,
                setPages: function (extra) {
                  commands = buildCommands(mergePages(DEFAULT_PAGES, extra || [])); render();
                } };
    root.__plkCtl = ctl;
    return ctl;
  }

  pure.mount = mount;
  return pure;
});
