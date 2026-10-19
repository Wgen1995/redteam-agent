import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import MomentCard from "./MomentCard";
import { KINDS, kindSpec } from "./kinds";

/**
 * T7 两级播报测试(先红后绿):
 * - kinds 词表: G-r18 timeline 盘点出的全部 kind 逐一给指挥级一行人话
 *   (样例 detail 取自 tests/fixtures/G-r18/timeline.tsv 实行);引擎
 *   warrior 生命周期 kind(loop.py 落行同形)同盘;未知 kind 兜底
 *   「[kind] detail 原样」零编造。
 * - MomentCard: 一级=时间+kind 色标+人话;二级=点开原样
 *   detail/kind/key/battle(透明不藏);着色/权重分 kind。
 */

interface Row {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

const BASE: Row = {
  key: "k1",
  ts: "2026-10-14T11:00:00Z",
  kind: "add-finding",
  detail: "add-finding FD-r18-0001",
  battle: "battle-1",
  badge: "hsl(284, 70%, 60%)",
};

function rowOf(over: Partial<Row>): Row {
  return { ...BASE, ...over };
}

function renderCard(over: Partial<Row>, fresh = false) {
  const row = rowOf(over);
  const utils = render(<MomentCard row={row} fresh={fresh} />);
  return { ...utils, row };
}

// ---------------------------------------------------------------------------
// 词表盘点: 每条 = {kind, 样例 detail(夹具实行), 期望一级人话(锁定词表)}。
// ---------------------------------------------------------------------------

const CATALOG: { kind: string; detail: string; line: string }[] = [
  { kind: "add-goal", detail: "add-goal G-r18-0001", line: "作战目标立卡 G-r18-0001" },
  { kind: "add-scope", detail: "add-scope S-r18-0001", line: "划定打击范围 S-r18-0001" },
  {
    kind: "egress-compile",
    detail: "egress-compile acl=egress.acl lines=41",
    line: "出网白名单编制就位(41 条规则)",
  },
  {
    kind: "gate-exit",
    detail: "gate-exit:P0 asserts=3 result=PASS",
    line: "P0 关卡通过(3 项断言)",
  },
  {
    kind: "add-intent",
    detail: "add-intent INT-r18-0001",
    line: "作战意图立案 INT-r18-0001",
  },
  {
    kind: "add-asset",
    detail: "add-asset AST-r18-0001(in_scope)",
    line: "目标资产入册 AST-r18-0001(in_scope)",
  },
  { kind: "add-fact", detail: "add-fact F-r18-0001", line: "情报落账 F-r18-0001" },
  {
    kind: "gate-fail",
    detail:
      "gate-fail:P1 assert=ledger-tree-check reason=FAIL\nAST-r18-0001(type=service) 缺 parent 边\nAST-r18-0002(type=service) 缺 parent 边",
    line: "P1 关卡未过: ledger-tree-check(明细见原文)",
  },
  {
    kind: "add-edge",
    detail: "add-edge E-r18-0001(parent)",
    line: "目标关系连线 E-r18-0001(parent)",
  },
  {
    kind: "matrix-init",
    detail: "matrix-init vocab=WSTG-v4.2 sha=980473723d2a surfaces=8 classes=12",
    line: "作战矩阵初始化: WSTG-v4.2(8 面/12 类)",
  },
  { kind: "matrix-freeze", detail: "matrix-freeze rows=96", line: "作战矩阵冻结定盘(96 格)" },
  {
    kind: "add-evidence",
    detail: "add-evidence EV-r18-0001",
    line: "证据入袋 EV-r18-0001",
  },
  { kind: "add-finding", detail: "add-finding FD-r18-0001", line: "新发现 FD-r18-0001" },
  {
    kind: "request",
    detail: "request: svc-login/login via=replay",
    line: "回放请求 svc-login/login(via=replay)",
  },
  {
    kind: "replay-probe",
    detail: "replay-probe EV-r18-0001 verdict=reproduced",
    line: "复放探针 EV-r18-0001: 重现成功",
  },
  {
    kind: "replay-probe",
    detail: "replay-probe EV-r18-0097 verdict=not-reproduced",
    line: "复放探针 EV-r18-0097: 未能重现",
  },
  {
    kind: "add-cred",
    detail: "add-cred CRED-r18-0001",
    line: "凭据入库 CRED-r18-0001",
  },
  {
    kind: "supersede-finding",
    detail: "supersede-finding FD-r18-0006->FD-r18-0036",
    line: "发现更替 FD-r18-0006→FD-r18-0036",
  },
  { kind: "budget-log", detail: "budget-log goal", line: "预算播报(明细见原文)" },
  { kind: "matrix-set-batch", detail: "matrix-set-batch n=96", line: "作战矩阵就位(96 项)" },
  {
    kind: "replay",
    detail: "replay:EV-r18-0001:VERIFIED",
    line: "机器复放验真 EV-r18-0001 已验",
  },
  {
    kind: "replay",
    detail: "replay:EV-r18-0011:REJECTED",
    line: "机器复放验真 EV-r18-0011 复放未过",
  },
  {
    kind: "warrior-start",
    detail: "warrior-start battle=3 warrior=W-abc pid=123 channels=3 cap=500000",
    line: "兵种出动 W-abc",
  },
  {
    kind: "warrior-heartbeat",
    detail: "warrior-heartbeat warrior=W-abc intent=INT-r18-0001",
    line: "士兵心跳 W-abc(在跑)",
  },
  {
    kind: "warrior-stop",
    detail: "warrior-stop warrior=W-abc reason=round-limit round 8/8",
    line: "士兵收兵 W-abc(原因 round-limit)",
  },
  {
    kind: "warrior-yield",
    detail: "warrior-yield warrior=W-1 intent=INT-2 to=W-9",
    line: "士兵移交 W-1→W-9",
  },
  {
    kind: "warrior-stall",
    detail: "warrior-stall warrior=W-abc detail=两轮无进展",
    line: "士兵停滞告警 W-abc",
  },
];

describe("时刻卡 kinds 词表(G-r18 全量盘点)", () => {
  afterEach(cleanup);

  it.each(CATALOG)("$kind → $line", ({ kind, detail, line }) => {
    renderCard({ kind, detail });
    expect(screen.getByTestId("moment-line").textContent).toBe(line);
  });

  it("词表完备: CATALOG 覆盖 KINDS 全部键,逐项产非空行(无 undefined 泄漏)", () => {
    const catalogKinds = new Set(CATALOG.map((c) => c.kind));
    const samples = new Map(CATALOG.map((c) => [c.kind, c.detail]));
    expect([...KINDS.keys()].sort()).toEqual([...catalogKinds].sort());
    for (const [kind, spec] of KINDS) {
      const line = spec.line(samples.get(kind) ?? kind);
      expect(line.length).toBeGreaterThan(0);
      expect(line).not.toMatch(/undefined|null|NaN/);
    }
  });

  it("未知 kind 兜底: [kind] detail 原样,零编造,中性着色", () => {
    renderCard({ kind: "nmap-sweep", detail: "nmap -p 1-1000 demo.io" });
    expect(screen.getByTestId("moment-line").textContent).toBe(
      "[nmap-sweep] nmap -p 1-1000 demo.io",
    );
    const card = screen.getByTestId("row-k1");
    expect(card.className).toContain("text-tx3");
    expect(card.className).not.toContain("text-dang");
  });

  it("kindSpec 查询: 已知 kind 命中词表,未知 kind 走兜底", () => {
    expect(KINDS.has("add-finding")).toBe(true);
    const fb = kindSpec("never-seen-op");
    expect(fb.weight).toBe("normal");
    expect(fb.line("raw payload")).toBe("[never-seen-op] raw payload");
  });
});

describe("MomentCard 两级播报", () => {
  afterEach(cleanup);

  it("一级: 时间(HH:MM:SS)+kind 色标(title=kind)+人话+battle 徽标点", () => {
    renderCard({});
    const card = screen.getByTestId("row-k1");
    expect(card).toHaveAttribute("data-kind", "add-finding");
    expect(screen.getByTestId("moment-time").textContent).toBe("11:00:00");
    expect(screen.getByTestId("moment-time")).toHaveAttribute("title", BASE.ts);
    const mark = screen.getByTestId("moment-mark");
    expect(mark).toHaveAttribute("title", "add-finding");
    expect(screen.getByTestId("moment-line").textContent).toBe("新发现 FD-r18-0001");
    const dot = screen.getByTestId("battle-dot");
    expect(dot).toHaveAttribute("title", "battle-1");
    expect(dot).toHaveStyle({ backgroundColor: "hsl(284, 70%, 60%)" });
  });

  it("二级: 点开原样 detail/kind/key/battle(透明不藏),再点收起", () => {
    renderCard({});
    const toggle = screen.getByTestId("moment-toggle");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("moment-raw")).not.toBeInTheDocument();
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const raw = screen.getByTestId("moment-raw");
    expect(raw).toHaveTextContent(BASE.detail);
    expect(raw).toHaveTextContent("kind: add-finding");
    expect(raw).toHaveTextContent("key: k1");
    expect(raw).toHaveTextContent("battle: battle-1");
    fireEvent.click(toggle);
    expect(screen.queryByTestId("moment-raw")).not.toBeInTheDocument();
  });

  it("多行原文逐字保留(gate-fail reason 不截断)", () => {
    renderCard({
      kind: "gate-fail",
      detail:
        "gate-fail:P1 assert=ledger-tree-check reason=FAIL\nAST-r18-0001(type=service) 缺 parent 边\nAST-r18-0002(type=service) 缺 parent 边",
    });
    // 一级只给人话一句
    expect(screen.getByTestId("moment-line").textContent).toBe(
      "P1 关卡未过: ledger-tree-check(明细见原文)",
    );
    fireEvent.click(screen.getByTestId("moment-toggle"));
    const raw = screen.getByTestId("moment-raw");
    expect(raw).toHaveTextContent("AST-r18-0001(type=service) 缺 parent 边");
    expect(raw).toHaveTextContent("AST-r18-0002(type=service) 缺 parent 边");
  });

  it("着色分 kind: 发现红/验真绿/未知中性", () => {
    const { unmount: u1 } = renderCard({ key: "r1", kind: "add-finding", detail: "add-finding FD-1" });
    expect(screen.getByTestId("row-r1").className).toContain("text-dang");
    expect(screen.getByTestId("row-r1").className).toContain("border-dang");
    u1();
    const { unmount: u2 } = renderCard({ key: "r2", kind: "replay", detail: "replay:EV-1:VERIFIED" });
    expect(screen.getByTestId("row-r2").className).toContain("text-ok");
    u2();
    renderCard({ key: "r3", kind: "mystery", detail: "opaque" });
    expect(screen.getByTestId("row-r3").className).toContain("text-tx3");
  });

  it("权重分 kind: 发现/关卡/验真 loud,心跳 dim 轻描", () => {
    const { unmount: u1 } = renderCard({ key: "w1", kind: "add-finding", detail: "add-finding FD-1" });
    expect(screen.getByTestId("row-w1")).toHaveAttribute("data-weight", "loud");
    u1();
    const { unmount: u2 } = renderCard({ key: "w2", kind: "gate-exit", detail: "gate-exit:P0 asserts=3 result=PASS" });
    expect(screen.getByTestId("row-w2")).toHaveAttribute("data-weight", "loud");
    u2();
    const { unmount: u3 } = renderCard({ key: "w3", kind: "replay", detail: "replay:EV-1:VERIFIED" });
    expect(screen.getByTestId("row-w3")).toHaveAttribute("data-weight", "loud");
    u3();
    renderCard({ key: "w4", kind: "warrior-heartbeat", detail: "warrior-heartbeat warrior=W-1" });
    const hb = screen.getByTestId("row-w4");
    expect(hb).toHaveAttribute("data-weight", "dim");
    expect(hb.className).toContain("opacity-55"); // 轻描
  });

  it("fresh 新行淡入标记透传(chat 流新行动画)", () => {
    renderCard({ key: "f1" }, true);
    expect(screen.getByTestId("row-f1").className).toContain("row-fade");
  });
});
