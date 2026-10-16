"use strict";
/* tanyin-web status.js · 状态语义单源（v0.9d 收口批切全站外链）
   语义照 ARTEX status.ts「状态先讲清语义边界再上色」——抄语义不抄代码：
   阶段进度（九步）/ 证据复测结果 / 覆盖表格态 → 中文标签+tone 一处定义，七页共用。
   本文件即单源；页面 <head> 外链引用（URL=/status.js，
   server.py 白名单句柄字节级伺服本文件——E3 评审 F2 裁决）。
   copy-v09d 批：用户可见文案全部换人话（门名去「门」字系，内部代号只留在注释里）。 */

var TY = window.TY || {};

/* 九步阶段：id 全序与 phases/phases.yaml 的 states 一致；
   中文名=人话显示层（yaml 里的 title 是内部代号，不直出用户面） */
TY.NINE_GATES = [
  { id: "P0", name: "授权确认" },
  { id: "P1", name: "信息收集" },
  { id: "P2", name: "规划" },
  { id: "P3", name: "循环测试" },
  { id: "P4", name: "汇总" },
  { id: "P5", name: "报告" },
  { id: "P5.5", name: "报告签发" },
  { id: "P6.0", name: "收尾清理" },
  { id: "P6", name: "成果归档" }
];

/* 阶段状态：通过=绿 / 未通过=红 / 未开始=灰 */
TY.GATE_STATE = {
  "PASS": { label: "通过", tone: "ok" },
  "FAIL": { label: "未通过", tone: "bad" },
  "PENDING": { label: "未开始", tone: "idle" }
};

/* 证据复测结果：空串=还没复测（战斗记录里没有对应的复测行） */
TY.REPLAY_STATE = {
  "reproduced": { label: "已复现", tone: "ok" },
  "not-reproduced": { label: "未复现", tone: "bad" },
  "manual": { label: "需人工", tone: "warn" },
  "env-diff": { label: "环境差异", tone: "warn" },
  "": { label: "未复测", tone: "idle" }
};

/* 覆盖表格态：空格=还没测（测试覆盖表三态语义） */
TY.CELL_STATE = {
  "cold": { label: "已测", tone: "ok" },
  "frozen": { label: "已锁定", tone: "info" },
  "empty": { label: "未测", tone: "bad" }
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
  if (text !== undefined && text !== null) {
    /* 热修: 文本必须落 .state-msg 子节点——旧实现 box.textContent=text 会吃掉
       .content/.skeleton 子树,后续渲染 querySelector(".content") 得 null 即崩
       (session 页三块全崩根因,2026-10-16 视觉评审舰 DOM 普查抓获) */
    var msg = box.querySelector(".state-msg");
    if (!msg) {
      msg = document.createElement("p");
      msg.className = "state-msg";
      box.appendChild(msg);
    }
    msg.textContent = text;
  }
  return box;
};

TY.failText = function (err) {
  return "加载失败：" + err + "（自动重试，画面保留上次数据）";
};

/* 载入即恢复主题（<head> 外链早于正文绘制——深色用户不白闪）。
   v0.9d 收口批顺修：此前 bootTheme() 只调用未定义，每页尾部抛 TypeError。 */
TY.bootTheme = function () {
  return TY.applyTheme(TY.savedTheme());
};

TY.bootTheme();
