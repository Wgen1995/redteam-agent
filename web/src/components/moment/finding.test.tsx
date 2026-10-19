import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import FindingCard, { findingRefOf, type FindingDoc } from "./FindingCard";

/**
 * T9 发现时刻卡测试(先红后绿):
 * - 配对升级: add-finding/supersede-finding 行配到 /api/chat/findings 的
 *   发现 → 升级为发现卡(发现号+标题+严重度章+验真态徽);
 * - 四色严重度章: 引擎 confidence 词表 C1/C2/C3/➖🛑 → critical/high/
 *   medium/low 四色;词表外原样透传不翻译(不硬凑);
 * - 三态验真徽: 已验→绿「机器已验」;REPAIRED→绿「复放确认」;其余
 *   (待验/复验中/REJECTED)→灰「待机器复验」如实,不造绿;
 * - 配不到回退: finding=null → 退回 T7 MomentCard 原卡不硬凑;
 * - 二级: 点开原文逐字+证据袋引用(有则显,无则不占位)+kind/key/battle。
 */

interface Row {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

const ADD_ROW: Row = {
  key: "k1",
  ts: "2026-10-14T13:30:00Z",
  kind: "add-finding",
  detail: "add-finding FD-r18-0076",
  battle: "battle-1",
  badge: "hsl(284, 70%, 60%)",
};

const SUPERSEDE_ROW: Row = {
  key: "k2",
  ts: "2026-10-14T13:30:01Z",
  kind: "supersede-finding",
  detail: "supersede-finding FD-r18-0047->FD-r18-0076",
  battle: "battle-1",
  badge: "hsl(284, 70%, 60%)",
};

function docOf(over: Partial<FindingDoc>): FindingDoc {
  return {
    id: "FD-r18-0076",
    title: "command-injection beacon face diag (execution unproven)",
    severity: "C1",
    where: "AST-r18-0037",
    verified: false,
    replay_state: "复验中",
    evidence: ["EV-r18-0102"],
    battle: "battle-1",
    badge: "hsl(284, 70%, 60%)",
    ts: "2026-10-14T13:30:00Z",
    ...over,
  };
}

function renderCard(row: Row, finding: FindingDoc | null, fresh = false) {
  return render(<FindingCard row={row} finding={finding} fresh={fresh} />);
}

describe("findingRefOf: FD 号从 detail 确定性解析", () => {
  it("add-finding → FD 号;supersede-finding → 箭头目标(更替后在册)", () => {
    expect(findingRefOf("add-finding", "add-finding FD-r18-0076")).toBe("FD-r18-0076");
    expect(findingRefOf("supersede-finding", "supersede-finding FD-a-1->FD-b-2"))
      .toBe("FD-b-2");
  });
  it("其他 kind / 解析不中 → null(不硬凑)", () => {
    expect(findingRefOf("add-evidence", "add-evidence EV-1")).toBeNull();
    expect(findingRefOf("add-finding", "note without ref")).toBeNull();
    expect(findingRefOf("supersede-finding", "supersede-finding 乱形")).toBeNull();
  });
});

describe("FindingCard: 配对升级", () => {
  afterEach(cleanup);

  it("add-finding 配到发现 → 发现卡: 发现号+标题+battle 点+时间", () => {
    renderCard(ADD_ROW, docOf({}));
    const card = screen.getByTestId("finding-card");
    expect(card).toHaveAttribute("data-fd", "FD-r18-0076");
    expect(within(card).getByTestId("finding-id")).toHaveTextContent("FD-r18-0076");
    expect(within(card).getByTestId("finding-title"))
      .toHaveTextContent("command-injection beacon face diag");
    expect(within(card).getByTestId("battle-dot")).toHaveAttribute("title", "battle-1");
    expect(within(card).getByTestId("moment-time")).toHaveTextContent("13:30:00");
    // add-finding=词表 loud → 加重
    expect(card.className).toContain("font-medium");
  });

  it("supersede-finding 行升级到箭头目标发现,并注明更替来源", () => {
    renderCard(SUPERSEDE_ROW, docOf({}));
    const card = screen.getByTestId("finding-card");
    expect(card).toHaveAttribute("data-fd", "FD-r18-0076");
    expect(within(card).getByText(/更替自 FD-r18-0047/)).toBeInTheDocument();
  });

  it("fresh 新行淡入标记透传", () => {
    renderCard(ADD_ROW, docOf({}), true);
    expect(screen.getByTestId("finding-card").className).toContain("row-fade");
  });
});

describe("FindingCard: 四色严重度章", () => {
  afterEach(cleanup);

  it("C1→危(critical 红)/C2→高(high 琥珀)/C3→中(medium 蓝)/➖🛑→低(low 灰)", () => {
    const cases: [string, string, string][] = [
      ["C1", "critical", "text-dang"],
      ["C2", "high", "text-warn"],
      ["C3", "medium", "text-info"],
      ["➖🛑", "low", "text-tx3"],
    ];
    for (const [sev, tier, cls] of cases) {
      cleanup();
      renderCard(ADD_ROW, docOf({ severity: sev, verified: true, replay_state: "已验" }));
      const chip = screen.getByTestId("sev-chip");
      expect(chip, `sev=${sev} 须 tier=${tier}`).toHaveAttribute("data-sev", tier);
      expect(chip.className).toContain(cls);
      expect(chip).toHaveTextContent(sev);           // 引擎词表原样同显
    }
  });

  it("词表外 severity 原样透传不翻译(不硬凑四色)", () => {
    renderCard(ADD_ROW, docOf({ severity: "高", verified: true, replay_state: "已验" }));
    const chip = screen.getByTestId("sev-chip");
    expect(chip).toHaveAttribute("data-sev", "other");
    expect(chip).toHaveTextContent("高");
    expect(chip.className).toContain("text-tx3");
  });

  it("severity 缺(None)→不出章,不造级", () => {
    renderCard(ADD_ROW, docOf({ severity: null, verified: true, replay_state: "已验" }));
    expect(screen.queryByTestId("sev-chip")).not.toBeInTheDocument();
  });
});

describe("FindingCard: 三态验真徽(不造绿)", () => {
  afterEach(cleanup);

  it("已验(verified)→绿「机器已验」", () => {
    renderCard(ADD_ROW, docOf({ verified: true, replay_state: "已验" }));
    const chip = screen.getByTestId("verify-chip");
    expect(chip).toHaveAttribute("data-state", "verified");
    expect(chip).toHaveTextContent("机器已验");
    expect(chip.className).toContain("text-ok");
  });

  it("REPAIRED→绿「复放确认」", () => {
    renderCard(ADD_ROW, docOf({ verified: true, replay_state: "REPAIRED" }));
    const chip = screen.getByTestId("verify-chip");
    expect(chip).toHaveAttribute("data-state", "repaired");
    expect(chip).toHaveTextContent("复放确认");
    expect(chip.className).toContain("text-ok");
  });

  it("复验中/待验/REJECTED→灰「待机器复验」,无绿", () => {
    for (const state of ["复验中", "待验", "REJECTED"]) {
      cleanup();
      renderCard(ADD_ROW, docOf({ verified: false, replay_state: state }));
      const chip = screen.getByTestId("verify-chip");
      expect(chip, `state=${state} 须灰`).toHaveAttribute("data-state", "pending");
      expect(chip).toHaveTextContent("待机器复验");
      expect(chip.className).not.toContain("text-ok");
      expect(chip.className).toContain("text-tx3");
    }
  });
});

describe("FindingCard: 配不到回退 T7 原卡", () => {
  afterEach(cleanup);

  it("finding=null → MomentCard 原样(一级人话+二级原文),无发现卡元素", () => {
    renderCard(ADD_ROW, null);
    expect(screen.queryByTestId("finding-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("moment-line")).toHaveTextContent("新发现 FD-r18-0076");
    expect(screen.queryByTestId("sev-chip")).not.toBeInTheDocument();
    expect(screen.queryByTestId("verify-chip")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("moment-toggle"));
    expect(screen.getByTestId("moment-raw")).toHaveTextContent("add-finding FD-r18-0076");
  });
});

describe("FindingCard: 二级(点开)", () => {
  afterEach(cleanup);

  it("原文逐字+证据袋引用+位置+kind/key/battle 透明不藏", () => {
    renderCard(ADD_ROW, docOf({}));
    fireEvent.click(screen.getByTestId("finding-toggle"));
    const raw = screen.getByTestId("finding-raw");
    expect(raw).toHaveTextContent("add-finding FD-r18-0076");   // 原文
    expect(within(raw).getByTestId("finding-evidence"))
      .toHaveTextContent("EV-r18-0102");                        // 证据袋引用
    expect(within(screen.getByTestId("finding-card")).getByTestId("finding-where"))
      .toHaveTextContent("AST-r18-0037");                       // 位置(一级)
    expect(raw).toHaveTextContent("kind: add-finding");
    expect(raw).toHaveTextContent("key: k1");
    expect(raw).toHaveTextContent("battle: battle-1");
  });

  it("多证据引用全列;无引用不出「证据袋」行(有则显)", () => {
    renderCard(ADD_ROW, docOf({ evidence: ["EV-r18-0097", "EV-r18-0098"] }));
    fireEvent.click(screen.getByTestId("finding-toggle"));
    expect(screen.getByTestId("finding-evidence"))
      .toHaveTextContent("EV-r18-0097");
    expect(screen.getByTestId("finding-evidence"))
      .toHaveTextContent("EV-r18-0098");
    cleanup();
    renderCard(ADD_ROW, docOf({ evidence: [] }));
    fireEvent.click(screen.getByTestId("finding-toggle"));
    expect(screen.queryByTestId("finding-evidence")).not.toBeInTheDocument();
  });

  it("多行原文 whitespace-pre-wrap 逐字保留", () => {
    const NL = String.fromCharCode(10);
    const row = { ...ADD_ROW, detail: "add-finding FD-r18-0076" + NL + "second line	tab" };
    renderCard(row, docOf({}));
    fireEvent.click(screen.getByTestId("finding-toggle"));
    const raw = screen.getByTestId("finding-raw");
    const dd = raw.querySelector("dd");
    expect(dd).not.toBeNull();
    expect(dd?.className).toContain("whitespace-pre-wrap");
    expect(dd?.textContent).toBe("add-finding FD-r18-0076\nsecond line	tab");
  });
});
