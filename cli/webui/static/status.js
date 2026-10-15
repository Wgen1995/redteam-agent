"use strict";
/* tanyin-web status.js · 状态语义单源（v0.9d ZhulongFire 换肤批）
   语义照 ARTEX status.ts「状态先讲清语义边界再上色」——抄语义不抄代码：
   九门门态 / 证据重放态 / 矩阵格态 → 中文标签+tone 一处定义，五页共用。
   本文件即单源；五页 <head> 内嵌字节级副本（tests/test_v09d_skin.py 字节钉同步——
   常驻 0.9c 老进程无 /status.js 路由，页面必须完全自包含，不得外链引用本文件）。 */

var TY = window.TY || {};

/* 九门：id+中文名 —— 与 phases/phases.yaml 的 states 全序 + gates.title 一致 */
TY.NINE_GATES = [
  { id: "P0", name: "授权门" },
  { id: "P1", name: "测绘" },
  { id: "P2", name: "规划" },
  { id: "P3", name: "演进循环" },
  { id: "P4", name: "汇总" },
  { id: "P5", name: "报告" },
  { id: "P5.5", name: "签发门" },
  { id: "P6.0", name: "清理门" },
  { id: "P6", name: "沉淀" }
];

/* 门态：过门=绿 / 拦下=红 / 未到=灰（label=单字徽章文案） */
TY.GATE_STATE = {
  "PASS": { label: "过", tone: "ok" },
  "FAIL": { label: "拦", tone: "bad" },
  "PENDING": { label: "待", tone: "idle" }
};

/* 证据重放态：空串=未重放（timeline 无对应 replay-probe 行） */
TY.REPLAY_STATE = {
  "reproduced": { label: "已复现", tone: "ok" },
  "not-reproduced": { label: "未复现", tone: "bad" },
  "manual": { label: "人工", tone: "warn" },
  "env-diff": { label: "环境差异", tone: "warn" },
  "": { label: "未重放", tone: "idle" }
};

/* 矩阵格态：空格=欠账（覆盖热图三态语义） */
TY.CELL_STATE = {
  "cold": { label: "已置格", tone: "ok" },
  "frozen": { label: "冻结格", tone: "info" },
  "empty": { label: "欠账空格", tone: "bad" }
};

/* 主题：浅色默认 + 深色镜像（CSS 变量同名成对）；localStorage 记忆——偏好只存本浏览器 */
TY.THEME_KEY = "tanyin-theme";

TY.applyTheme = function (theme) {
  var t = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
  return t;
};

TY.savedTheme = function () {
  try { return window.localStorage.getItem(TY.THEME_KEY); }
  catch (err) { return null; }               /* 隐私模式禁存：回浅色默认 */
};

TY.toggleTheme = function () {
  var now = document.documentElement.getAttribute("data-theme") === "dark"
    ? "light" : "dark";
  TY.applyTheme(now);
  try { window.localStorage.setItem(TY.THEME_KEY, now); }
  catch (err) { /* 存不进也照样换肤 */ }
  return now;
};

TY.syncThemeButton = function (btn) {
  if (!btn) { return; }
  var dark = document.documentElement.getAttribute("data-theme") === "dark";
  btn.textContent = dark ? "浅色" : "深色";
  btn.setAttribute("aria-label", dark ? "切换到浅色主题" : "切换到深色主题");
};

/* 四态纪律：骨架/加载/空/错误 —— 一处实现五页共用（骨架=静默灰条占位，零动效） */
TY.setState = function (box, state, text) {
  if (!box) { return null; }
  box.setAttribute("data-state", state);
  if (text !== undefined && text !== null) { box.textContent = text; }
  return box;
};

TY.failText = function (err) {
  return "加载失败：" + err + "（自动重试，画面保留上次数据）";
};

/* 载入即恢复主题（内嵌于 <head>，早于正文绘制——深色用户不白闪） */
TY.bootTheme();
