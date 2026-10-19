/**
 * 时刻卡 kinds 词表(T7 两级播报)——引擎 kind → {人话模板, 着色, 权重}。
 *
 * 词表盘点来源(单源,禁编造):
 * - tests/fixtures/G-r18/timeline.tsv 全部 20 个 kind(经读面
 *   ledger_reader._event_kind 同法切头词: 首空白 token 再截首个冒号前段);
 * - 引擎战士生命周期 5 kind(cli/warrior/loop.py / heartbeat.py 落行同形,
 *   G-r18 夹具未含、活体仗账本实有): warrior-start/-stop/-stall/-yield/
 *   -heartbeat(心跳=高频噪音,weight=dim 轻描)。
 * - 样例 detail 与模板逐条在 moment.test.tsx CATALOG 锁定(人话词表纪律)。
 *
 * 铁律: 模板解析失败(正则不中)→退回「[kind] detail 原样」兜底,零编造;
 * 着色走 GL-DS 状态色 token(与 chat 页旧 kindClass 同族词表)。
 */

/** 权重: loud=指挥必读(加重)/normal=常规/dim=轻描(高频心跳类压暗)。 */
export type MomentWeight = "loud" | "normal" | "dim";

export interface KindSpec {
  /** 一级人话一行: 从引擎 detail 确定性解析,解析不中→原样兜底。 */
  line: (detail: string) => string;
  /** GL-DS 着色(border+text token 对;分支型 kind 按 detail 判读)。 */
  tone: (detail: string) => string;
  /** 展示权重(轻描/加重)。 */
  weight: MomentWeight;
}

const TONE = {
  acc: "border-acc/40 text-acc",
  ok: "border-ok/40 text-ok",
  info: "border-info/40 text-info",
  warn: "border-warn/40 text-warn",
  dang: "border-dang/40 text-dang",
  neutral: "border-line-2 text-tx3",
} as const;

/** 首个捕获组;不中→null。 */
function grab(re: RegExp, detail: string): string | null {
  const m = re.exec(detail);
  return m ? m[1] : null;
}

function grab2(re: RegExp, detail: string): [string, string] | null {
  const m = re.exec(detail);
  return m ? [m[1], m[2]] : null;
}

/** 引擎复放终态(check_cmds REPLAY_STATES 同源枚举)→人话。 */
function replayStateWord(state: string): string {
  if (state === "VERIFIED") return "已验";
  if (state === "REPAIRED") return "修复后过验";
  if (state === "REJECTED") return "复放未过";
  return state;
}

/** 词表: kind → 指挥级一行人话+着色+权重(盘点来源见文件头)。 */
export const KINDS: Map<string, KindSpec> = new Map([
  // ---- 仗开局 ----
  ["add-goal", {
    line: (d) => {
      const id = grab(/(?:^|\s)(G-\S+)/, d);
      return id ? "作战目标立卡 " + id : "[add-goal] " + d;
    },
    tone: () => TONE.acc,
    weight: "loud",
  }],
  ["add-scope", {
    line: (d) => {
      const id = grab(/(?:^|\s)(S-\S+)/, d);
      return id ? "划定打击范围 " + id : "[add-scope] " + d;
    },
    tone: () => TONE.acc,
    weight: "normal",
  }],
  ["add-intent", {
    line: (d) => {
      const id = grab(/(?:^|\s)(INT-\S+)/, d);
      return id ? "作战意图立案 " + id : "[add-intent] " + d;
    },
    tone: () => TONE.info,
    weight: "normal",
  }],
  // ---- 目标面(资产/关系/情报/凭据/出网) ----
  ["add-asset", {
    line: (d) => {
      const id = grab(/(?:^|\s)(AST-\S+)/, d);
      return id ? "目标资产入册 " + id : "[add-asset] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["add-edge", {
    line: (d) => {
      const id = grab(/(?:^|\s)(E-\S+)/, d);
      return id ? "目标关系连线 " + id : "[add-edge] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["add-fact", {
    line: (d) => {
      const id = grab(/(?:^|\s)(F-\S+)/, d);
      return id ? "情报落账 " + id : "[add-fact] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["add-cred", {
    line: (d) => {
      const id = grab(/(?:^|\s)(CRED-\S+)/, d);
      return id ? "凭据入库 " + id : "[add-cred] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["egress-compile", {
    line: (d) => {
      const n = grab(/lines=(\d+)/, d);
      return n ? "出网白名单编制就位(" + n + " 条规则)" : "[egress-compile] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  // ---- 作战矩阵 ----
  ["matrix-init", {
    line: (d) => {
      const vocab = grab(/vocab=(\S+)/, d);
      const surf = grab(/surfaces=(\d+)/, d);
      const cls = grab(/classes=(\d+)/, d);
      return vocab && surf && cls
        ? "作战矩阵初始化: " + vocab + "(" + surf + " 面/" + cls + " 类)"
        : "[matrix-init] " + d;
    },
    tone: () => TONE.info,
    weight: "normal",
  }],
  ["matrix-set-batch", {
    line: (d) => {
      const n = grab(/n=(\d+)/, d);
      return n ? "作战矩阵就位(" + n + " 项)" : "[matrix-set-batch] " + d;
    },
    tone: () => TONE.info,
    weight: "normal",
  }],
  ["matrix-freeze", {
    line: (d) => {
      const n = grab(/rows=(\d+)/, d);
      return n ? "作战矩阵冻结定盘(" + n + " 格)" : "[matrix-freeze] " + d;
    },
    tone: () => TONE.info,
    weight: "normal",
  }],
  // ---- 关卡 ----
  ["gate-exit", {
    line: (d) => {
      const phase = grab(/^gate-exit:(\S+)/, d);
      const asserts = grab(/asserts=(\d+)/, d);
      const result = grab(/result=(\S+)/, d);
      if (!phase || !asserts || !result) return "[gate-exit] " + d;
      return result === "PASS"
        ? phase + " 关卡通过(" + asserts + " 项断言)"
        : phase + " 关卡结果 " + result + "(" + asserts + " 项断言)";
    },
    tone: (d) => ((/(^|\s)result=PASS\b/).test(d) ? TONE.ok : TONE.dang),
    weight: "loud",
  }],
  ["gate-fail", {
    line: (d) => {
      const phase = grab(/^gate-fail:(\S+)/, d);
      const assert = grab(/\bassert=(\S+)/, d);
      return phase && assert
        ? phase + " 关卡未过: " + assert + "(明细见原文)"
        : "[gate-fail] " + d;
    },
    tone: () => TONE.dang,
    weight: "loud",
  }],
  // ---- 发现/证据/复放 ----
  ["add-finding", {
    line: (d) => {
      const id = grab(/(?:^|\s)(FD-\S+)/, d);
      return id ? "新发现 " + id : "[add-finding] " + d;
    },
    tone: () => TONE.dang,
    weight: "loud",
  }],
  ["supersede-finding", {
    line: (d) => {
      const m = grab2(/^supersede-finding\s+(\S+?)->(\S+)/, d);
      return m ? "发现更替 " + m[0] + "→" + m[1] : "[supersede-finding] " + d;
    },
    tone: () => TONE.warn,
    weight: "loud",
  }],
  ["add-evidence", {
    line: (d) => {
      const id = grab(/(?:^|\s)(EV-\S+)/, d);
      return id ? "证据入袋 " + id : "[add-evidence] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["replay-probe", {
    line: (d) => {
      const m = grab2(/^replay-probe\s+(\S+)\s+verdict=(\S+)/, d);
      if (!m) return "[replay-probe] " + d;
      const ref = m[0];
      const verdict = m[1];
      if (verdict === "reproduced") return "复放探针 " + ref + ": 重现成功";
      if (verdict === "not-reproduced") return "复放探针 " + ref + ": 未能重现";
      return "复放探针 " + ref + ": " + verdict;
    },
    tone: (d) =>
      /verdict=reproduced\b/.test(d)
        ? TONE.ok
        : /verdict=not-reproduced\b/.test(d)
          ? TONE.warn
          : TONE.info,
    weight: "normal",
  }],
  ["replay", {
    line: (d) => {
      const m = grab2(/^replay:(\S+):(\S+)/, d);
      return m
        ? "机器复放验真 " + m[0] + " " + replayStateWord(m[1])
        : "[replay] " + d;
    },
    tone: (d) => {
      const s = grab(/^replay:\S+:(\S+)/, d);
      return s === "VERIFIED" || s === "REPAIRED"
        ? TONE.ok
        : s === "REJECTED"
          ? TONE.dang
          : TONE.neutral;
    },
    weight: "loud",
  }],
  // ---- 动作/预算 ----
  ["request", {
    line: (d) => {
      const path = grab(/^request:\s*(\S+)/, d);
      if (!path) return "[request] " + d;
      const via = grab(/\svia=(\S+)/, d);
      return via ? "回放请求 " + path + "(via=" + via + ")" : "回放请求 " + path;
    },
    tone: () => TONE.info,
    weight: "normal",
  }],
  ["budget-log", {
    line: () => "预算播报(明细见原文)",
    tone: () => TONE.info,
    weight: "normal",
  }],
  // ---- 战士生命周期(引擎活体;G-r18 夹具未含) ----
  ["warrior-start", {
    line: (d) => {
      const w = grab(/warrior=(\S+)/, d);
      return w ? "兵种出动 " + w : "[warrior-start] " + d;
    },
    tone: () => TONE.acc,
    weight: "loud",
  }],
  ["warrior-heartbeat", {
    line: (d) => {
      const w = grab(/warrior=(\S+)/, d);
      return w ? "士兵心跳 " + w + "(在跑)" : "[warrior-heartbeat] " + d;
    },
    tone: () => TONE.neutral,
    weight: "dim",
  }],
  ["warrior-stop", {
    line: (d) => {
      const w = grab(/warrior=(\S+)/, d);
      if (!w) return "[warrior-stop] " + d;
      const reason = grab(/\sreason=(\S+)/, d);
      return reason ? "士兵收兵 " + w + "(原因 " + reason + ")" : "士兵收兵 " + w;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["warrior-yield", {
    line: (d) => {
      const w = grab(/warrior=(\S+)/, d);
      const to = grab(/\sto=(\S+)/, d);
      return w && to ? "士兵移交 " + w + "→" + to : "[warrior-yield] " + d;
    },
    tone: () => TONE.neutral,
    weight: "normal",
  }],
  ["warrior-stall", {
    line: (d) => {
      const w = grab(/warrior=(\S+)/, d);
      return w ? "士兵停滞告警 " + w : "[warrior-stall] " + d;
    },
    tone: () => TONE.warn,
    weight: "normal",
  }],
] as [string, KindSpec][]);

/** kind → 词表项;未知 kind 一律兜底「[kind] detail 原样」(中性/常规)。 */
export function kindSpec(kind: string): KindSpec {
  const hit = KINDS.get(kind);
  if (hit) return hit;
  return {
    line: (d) => "[" + kind + "] " + d,
    tone: () => TONE.neutral,
    weight: "normal",
  };
}
