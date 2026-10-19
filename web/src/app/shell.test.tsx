import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell";
import { ALL_ITEMS } from "./ia";
import ChatPage from "../pages/chat";
import PlaceholderPage from "../pages/placeholder";
import { DEMO_FLAG } from "../lib/api";

/** T4 壳测试: 20 页 IA 分组/激活态/占位空态/badge 数字来自 overview/失败不造假/demo 黄条挪顶栏。 */

const GROUP_NAMES: Record<string, string[]> = {
  作战: ["指挥台", "仪表盘", "任务", "发现", "资产与覆盖", "流量", "舰队"],
  机组: ["工具执行", "LLM录制", "报告", "知识库"],
  系统: ["智能体", "Skill", "能力", "拦截规则", "审批", "通知", "LLM连接", "日志", "设置"],
};

function renderShellAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/chat" element={<ChatPage />} />
          {ALL_ITEMS.filter((i) => i.path !== "/chat").map((i) => (
            <Route
              key={i.path}
              path={i.path}
              element={<PlaceholderPage name={i.name} hint={i.hint} />}
            />
          ))}
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

function mockOverview(body: unknown, ok = true) {
  return vi.fn().mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => body });
}

const deadFetch = () => vi.fn().mockRejectedValue(new Error("net down"));

describe("壳(20 页 IA 侧栏+顶栏)", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    cleanup();
  });

  it("分组渲染: 作战7/机组4/系统9 共 20 项,顶栏三件全占位,/chat 为实页非占位", () => {
    vi.stubGlobal("fetch", deadFetch());
    renderShellAt("/chat");

    for (const [label, names] of Object.entries(GROUP_NAMES)) {
      const group = screen.getByRole("group", { name: label });
      const links = within(group).getAllByRole("link");
      expect(links).toHaveLength(names.length);
      expect(links.map((a) => a.textContent?.replace(/\d+/, "").trim())).toEqual(names);
    }
    expect(screen.getByRole("navigation").querySelectorAll("a")).toHaveLength(20);

    // 顶栏三件: 搜索/预算表/全停,全为占位禁用态;全停 title=P1 接线
    expect(screen.getByRole("searchbox", { name: "全局搜索" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "预算表" })).toBeDisabled();
    const halt = screen.getByRole("button", { name: "全停" });
    expect(halt).toBeDisabled();
    expect(halt).toHaveAttribute("title", "P1 接线");

    // /chat 在壳内渲染实页,不是占位
    expect(screen.getByTestId("chat-page")).toBeInTheDocument();
    expect(screen.queryByTestId("placeholder-page")).not.toBeInTheDocument();
  });

  it("激活态: 当前页 aria-current=page,其余不高亮;占位页=页名+一句指路文案", () => {
    vi.stubGlobal("fetch", deadFetch());
    renderShellAt("/dashboard");

    expect(screen.getByRole("link", { name: "仪表盘" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      screen.getByRole("link", { name: "指挥台" }),
    ).not.toHaveAttribute("aria-current");

    const ph = screen.getByTestId("placeholder-page");
    expect(within(ph).getByText("仪表盘")).toBeInTheDocument();
    expect(
      within(ph).getByText("还没打过仗→去指挥台说一句打哪"),
    ).toBeInTheDocument();
  });

  it("badge 数字来自 mock overview: 指挥台=进行中仗数,审批红点=待审数", async () => {
    vi.stubGlobal(
      "fetch",
      mockOverview({ active_battles: 2, soldiers_running: 5, pending_approvals: 3 }),
    );
    renderShellAt("/chat");

    const battles = await screen.findByTestId("badge-battles");
    expect(battles).toHaveTextContent("2");
    expect(
      within(screen.getByRole("link", { name: /指挥台/ })).getByTestId("badge-battles"),
    ).toBeInTheDocument();

    const approvals = await screen.findByTestId("badge-approvals");
    expect(approvals).toHaveTextContent("3");
    expect(
      within(screen.getByRole("link", { name: /审批/ })).getByTestId("badge-approvals"),
    ).toBeInTheDocument();
    expect(approvals.className).toContain("dang");
  });

  it("overview 失败→静默藏 badge 不造假(链接名不带数字)", async () => {
    const fetchMock = deadFetch();
    vi.stubGlobal("fetch", fetchMock);
    renderShellAt("/chat");

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(screen.queryByTestId("badge-battles")).not.toBeInTheDocument();
    expect(screen.queryByTestId("badge-approvals")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "指挥台" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "审批" })).toBeInTheDocument();
  });

  it("overview 全零→也不显 badge(零不是事件)", async () => {
    vi.stubGlobal(
      "fetch",
      mockOverview({ active_battles: 0, soldiers_running: 0, pending_approvals: 0 }),
    );
    renderShellAt("/chat");

    await waitFor(() => expect(screen.queryByTestId("badge-battles")).toBeNull());
    expect(screen.queryByTestId("badge-approvals")).not.toBeInTheDocument();
  });

  it("demo 黄条挪入顶栏: glds.demo=1 时显示,缺省不显示", () => {
    vi.stubGlobal("fetch", deadFetch());

    sessionStorage.setItem(DEMO_FLAG, "1");
    const { unmount } = renderShellAt("/chat");
    const bar = within(screen.getByTestId("topbar")).getByRole("status");
    expect(bar).toHaveTextContent("演示模式:未设密钥");
    unmount();

    sessionStorage.removeItem(DEMO_FLAG);
    renderShellAt("/chat");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
