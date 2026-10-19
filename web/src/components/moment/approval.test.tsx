import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import ApprovalCard from "./ApprovalCard";

/**
 * T8 内联审批卡测试(先红后绿): 渲染/双钮流/提交中/结果态/失败重试。
 * 卡=自足组件: warboard approvals 待审项 → 命令原文/风险句(有则显)/
 * 关联发现(事件内 FD 引用,有则显) → 批准执行/拒绝双钮 → POST
 * /api/chat/approve → 结果态(绿已批准/红已拒绝)/失败红条重试。
 */

const BASE = {
  id: "c1b0f3d2",
  event: "http-get http://10.2.0.7:8080/admin",
  risk_line: "只读探测动作——界内可走预授权豁免",
  timeout_policy: "待审挂起超 30 分钟→保守跳过(超时保守策略)",
  ts: "2026-10-14T11:00:00Z",
  battle: "battle-2",
  badge: "hsl(3, 70%, 60%)",
};

type Resp = { ok: boolean; status: number; json: () => Promise<unknown> };
type Call = { url: string; method: string; body: unknown };

function makeFetch(routes: Record<string, unknown[]>): ReturnType<typeof vi.fn> & { calls: Call[] } {
  const calls: Call[] = [];
  const fn = vi.fn((input: RequestInfo | URL, init?: RequestInit): Promise<Resp> => {
    const url = String(input);
    const method = (init?.method as string) || "GET";
    let body: unknown = undefined;
    if (init?.body) {
      try { body = JSON.parse(String(init.body)); } catch { body = String(init.body); }
    }
    calls.push({ url, method, body });
    for (const [frag, queue] of Object.entries(routes)) {
      if (!url.includes(frag)) continue;
      const item = queue.length > 1 ? queue.shift() : queue[0];
      if (item && typeof item === "object" && "reject" in item) {
        return Promise.reject(new Error("net down"));
      }
      if (item && typeof item === "object" && "httpStatus" in item) {
        const err = item as { httpStatus: number; json: unknown };
        return Promise.resolve({ ok: false, status: err.httpStatus, json: async () => err.json });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => item });
    }
    return Promise.reject(new Error("no route: " + url));
  });
  return Object.assign(fn, { calls });
}

describe("T8 审批卡(渲染/双钮/提交中/结果/失败)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    cleanup();
  });

  it("渲染: 命令原文+风险句+超时策略+battle 徽标点+双钮", async () => {
    vi.stubGlobal("fetch", makeFetch({ "/api/chat/approve": [{ ok: true }] }));
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    const card = screen.getByTestId("approval-card");
    expect(card).toHaveTextContent(BASE.event);
    expect(within(card).getByTestId("approval-risk")).toHaveTextContent("只读探测");
    expect(within(card).getByTestId("approval-timeout")).toHaveTextContent("30 分钟");
    expect(within(card).getByTestId("battle-dot")).toHaveAttribute("title", "battle-2");
    expect(screen.getByTestId("approval-approve")).toHaveTextContent("批准执行");
    expect(screen.getByTestId("approval-reject")).toHaveTextContent("拒绝");
  });

  it("风险句缺(null)不造假: 无 risk 行;超时策略缺同律", async () => {
    vi.stubGlobal("fetch", makeFetch({ "/api/chat/approve": [{ ok: true }] }));
    await act(async () => {
      render(<ApprovalCard item={{ ...BASE, risk_line: null, timeout_policy: null }} />);
    });
    expect(screen.queryByTestId("approval-risk")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-timeout")).not.toBeInTheDocument();
  });

  it("关联发现: 事件含 FD 引用则显,无则不显", async () => {
    vi.stubGlobal("fetch", makeFetch({ "/api/chat/approve": [{ ok: true }] }));
    await act(async () => {
      render(<ApprovalCard item={{ ...BASE, event: "exploit FD-r18-0076 via curl" }} />);
    });
    expect(screen.getByTestId("approval-finding")).toHaveTextContent("FD-r18-0076");
    await act(async () => {
      cleanup();
      render(<ApprovalCard item={BASE} />);
    });
    expect(screen.queryByTestId("approval-finding")).not.toBeInTheDocument();
  });

  it("批准流: POST approve → 卡转绿已批准(带审批号),双钮撤", async () => {
    const fetchMock = makeFetch({
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0001", decision: "approve" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-approve"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/approve"));
    expect(call?.method).toBe("POST");
    expect(call?.body).toEqual({
      battle: "battle-2", command_hash: "c1b0f3d2", decision: "approve",
    });
    const done = screen.getByTestId("approval-done");
    expect(done).toHaveTextContent("已批准");
    expect(done).toHaveTextContent("AP-1-0001");
    expect(done.className).toContain("text-ok");
    expect(screen.queryByTestId("approval-approve")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-reject")).not.toBeInTheDocument();
  });

  it("拒绝流: POST reject → 卡转红已拒绝", async () => {
    const fetchMock = makeFetch({
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0002", decision: "reject" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-reject"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/approve"));
    expect(call?.body).toEqual({
      battle: "battle-2", command_hash: "c1b0f3d2", decision: "reject",
    });
    const done = screen.getByTestId("approval-done");
    expect(done).toHaveTextContent("已拒绝");
    expect(done.className).toContain("text-dang");
  });

  it("提交中: 双钮禁用+文案提交中…,回执后恢复", async () => {
    let resolvePost!: (v: Resp) => void;
    const pending = new Promise<Resp>((res) => { resolvePost = res; });
    const fn = vi.fn((_input: RequestInfo | URL): Promise<Resp> => pending);
    vi.stubGlobal("fetch", fn);
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-approve"));
    });
    expect(screen.getByTestId("approval-approve")).toBeDisabled();
    expect(screen.getByTestId("approval-reject")).toBeDisabled();
    expect(screen.getByTestId("approval-approve")).toHaveTextContent("提交中");
    await act(async () => {
      resolvePost({ ok: true, status: 200, json: async () => ({ ok: true, approval_id: "AP-9" }) });
    });
    expect(screen.getByTestId("approval-done")).toBeInTheDocument();
  });

  it("失败红条: 502 服务器原文不吞+重试成功转结果态", async () => {
    const fetchMock = makeFetch({
      "/api/chat/approve": [
        { httpStatus: 502, json: { error: "审批桥失败(rc=2): 引擎拒收审批" } },
        { ok: true, approval_id: "AP-1-0003", decision: "approve" },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-approve"));
    });
    const bar = screen.getByTestId("approval-error");
    expect(bar).toHaveAttribute("role", "alert");
    expect(bar).toHaveTextContent("审批桥失败");
    expect(bar).toHaveTextContent("引擎拒收审批");
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-retry"));
    });
    expect(screen.queryByTestId("approval-error")).not.toBeInTheDocument();
    expect(screen.getByTestId("approval-done")).toHaveTextContent("已批准");
  });

  it("网络失败红条: 网络错原文可见可重试", async () => {
    const fetchMock = makeFetch({
      "/api/chat/approve": [{ reject: true }, { ok: true, approval_id: "AP-1-0004" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ApprovalCard item={BASE} />);
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-reject"));
    });
    expect(screen.getByTestId("approval-error")).toHaveTextContent("网络失败");
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-retry"));
    });
    expect(screen.getByTestId("approval-done")).toHaveTextContent("已拒绝");
  });
});
