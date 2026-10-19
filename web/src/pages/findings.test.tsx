import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import FindingsPage from "./findings";

/**
 * T12 发现页测试(mock api,先红后绿):
 * 统计条 / 过滤章 / 列表 / 灰卡区(仅待验,空不占位) / 详情抽屉(证据袋
 * 明细+复放史) / 重验钮仅待验显 / 复验中态 / 失败红条。
 */

interface Finding {
  id: string; title: string; severity: string; where: string;
  verified: boolean; replay_state: string; evidence: string[];
  battle: string; badge: string; ts: string | null;
}

const F_VER: Finding = {
  id: "FD-r18-0075", title: "admin face exposed", severity: "C1",
  where: "AST-r18-0037", verified: true, replay_state: "已验",
  evidence: ["EV-r18-0041"], battle: "battle-1",
  badge: "hsl(284, 70%, 60%)", ts: "2026-10-14T13:30:00Z",
};
const F_PEND: Finding = {
  id: "FD-r18-0076", title: "command-injection beacon", severity: "C1",
  where: "AST-r18-0037", verified: false, replay_state: "待验",
  evidence: [], battle: "battle-1",
  badge: "hsl(284, 70%, 60%)", ts: "2026-10-14T13:29:00Z",
};

type Resp = { ok: boolean; status: number; json: () => Promise<unknown> };
const ok = (body: unknown): Resp => ({ ok: true, status: 200, json: () => Promise.resolve(body) });

let gets: Record<string, Resp> = {};
let posts: Record<string, Resp> = {};

const ALL_ROWS: Finding[] = [F_VER, F_PEND];

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const path = String(url).split("?")[0];
    if (path === "/api/findings" && !init?.method && !gets[path]) {
      const q = new URLSearchParams(String(url).split("?")[1] || "");
      const st = q.get("state") || "";
      const rows = st === "verified" ? ALL_ROWS.filter((f) => f.verified)
        : st === "pending" ? ALL_ROWS.filter((f) => !f.verified) : ALL_ROWS;
      return ok(rows);
    }
    if (init?.method === "POST") {
      const hit = posts[path];
      if (hit) return hit;
      return { ok: false, status: 404, json: () => Promise.resolve({}) } as Resp;
    }
    const hit = gets[path];
    if (hit) return hit;
    return { ok: false, status: 404, json: () => Promise.resolve({}) } as Resp;
  }));
  gets = {};
  posts = {};
});
afterEach(() => {
  vi.unstubAllGlobals();
  cleanup();
});

describe("T12 发现页", () => {
  it("统计条: 总/危高/已验/待验", async () => {
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByText("FD-r18-0075"));
    expect(screen.getByTestId("stat-total").textContent).toBe("2");
    expect(screen.getByTestId("stat-danger").textContent).toBe("2");
    expect(screen.getByTestId("stat-verified").textContent).toBe("1");
    expect(screen.getByTestId("stat-pending").textContent).toBe("1");
  });

  it("灰卡区仅待验,含重验钮;已验无钮", async () => {
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByTestId("grey-zone"));
    expect(screen.getByTestId("grey-zone").textContent).toContain("FD-r18-0076");
    expect(screen.getByTestId("reverify-FD-r18-0076")).toBeTruthy();
    expect(screen.queryByTestId("reverify-FD-r18-0075")).toBeNull();
  });

  it("状态过滤 pending 只留待验", async () => {
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByText("FD-r18-0075"));
    fireEvent.click(screen.getByTestId("chip-state-pending"));
    await waitFor(() => expect(screen.queryByText("FD-r18-0075")).toBeNull());
    expect(screen.getAllByText("FD-r18-0076").length).toBeGreaterThan(0);
  });

  it("详情抽屉: 证据袋明细+复放史", async () => {
    gets["/api/findings/FD-r18-0075"] = ok({
      ...F_VER,
      evidence_detail: [{ id: "EV-r18-0041", kind: "command", created: "2026-10-14T09:42:00Z", card_path: "evidence/EV-r18-0041.md" }],
      replay_history: [{ ev: "EV-r18-0041", seq: 1, verdict: "reproduced" }],
    });
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByText("FD-r18-0075"));
    fireEvent.click(screen.getByTestId("row-FD-r18-0075"));
    await waitFor(() => screen.getByTestId("drawer-FD-r18-0075"));
    expect(screen.getByTestId("drawer-FD-r18-0075").textContent).toContain("EV-r18-0041");
    expect(screen.getByTestId("drawer-FD-r18-0075").textContent).toContain("reproduced");
  });

  it("重验流: 复验中→结果行内;失败红条", async () => {
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByTestId("reverify-FD-r18-0076"));
    posts["/api/findings/FD-r18-0076/reverify"] = ok({
      ok: true, results: [], state_note: "回写走验证官 settle 门",
    });
    fireEvent.click(screen.getByTestId("reverify-FD-r18-0076"));
    await waitFor(() => screen.getByTestId("reverify-note"));
    expect(screen.getByTestId("reverify-note").textContent).toContain("settle 门");
  });

  it("重验 422 无证据卡: 红条显原文", async () => {
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByTestId("reverify-FD-r18-0076"));
    posts["/api/findings/FD-r18-0076/reverify"] = {
      ok: false, status: 422,
      json: () => Promise.resolve({ error: "该发现无绑定证据卡,无可复放" }),
    } as Resp;
    fireEvent.click(screen.getByTestId("reverify-FD-r18-0076"));
    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toContain("无绑定证据卡");
  });

  it("拉取失败红条", async () => {
    gets = { "/api/findings": { ok: false, status: 500, json: () => Promise.resolve({}) } as Resp };
    render(<MemoryRouter><FindingsPage /></MemoryRouter>);
    await waitFor(() => screen.getByRole("alert"));
  });
});
