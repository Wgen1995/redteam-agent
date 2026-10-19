import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import TasksPage from "./tasks";

/**
 * T11 任务列表页测试(mock api,先红后绿):
 * 首载渲染仗卡(名/状态章/徽标/兵数/发现数/最新时刻) / 状态章执行中
 * 绿·其余中性 / 点卡进详情深链 / 10s 轮询翻新状态如实 / 空态零假数 /
 * 拉取失败红条+行内重试。
 */

interface Battle {
  id: string;
  name: string;
  status: string;
  status_detail: string;
  running: boolean;
  badge: string;
  goal: string;
  soldiers_n: number;
  findings_n: number;
  latest_ts: string | null;
}

const B1: Battle = {
  id: "battle-1", name: "authorized-range.local", status: "执行中",
  status_detail: "已点火（runner 未完跑）", running: true,
  badge: "hsl(284, 70%, 60%)", goal: "G-r18", soldiers_n: 6,
  findings_n: 76, latest_ts: "2026-10-14T13:31:00Z",
};
const B2: Battle = {
  id: "battle-2", name: "10.2.0.7", status: "复测",
  status_detail: "执行完跑 · 待复测", running: false,
  badge: "hsl(3, 70%, 60%)", goal: "G-1", soldiers_n: 2,
  findings_n: 3, latest_ts: "2026-10-19T04:54:49Z",
};

type Resp = { ok: boolean; status: number; json: () => Promise<unknown> };

function resp(body: unknown): Resp {
  return { ok: true, status: 200, json: async () => body };
}

/** /api/tasks 路由 fetch mock;队列为空时重复末项;reject 项抛错。 */
function makeFetch(queue: unknown[]) {
  const calls: string[] = [];
  const fn = vi.fn((input: RequestInfo | URL): Promise<Resp> => {
    const url = String(input);
    calls.push(url);
    if (!url.includes("/api/tasks")) {
      return Promise.reject(new Error("no route: " + url));
    }
    const item = queue.length > 1 ? queue.shift() : queue[0];
    if (item && typeof item === "object" && "reject" in item) {
      return Promise.reject(new Error("net down"));
    }
    return Promise.resolve(resp(item));
  });
  return Object.assign(fn, { calls });
}

/** 壳内路由探针: 点卡后 probe-detail 出现=已跳 /tasks/:id。 */
function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/tasks" element={<TasksPage />} />
        <Route
          path="/tasks/:id"
          element={<div data-testid="probe-detail">detail</div>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("任务列表 T11(仗卡+状态章)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", makeFetch([{ battles: [B1, B2] }]));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("首载渲染仗卡: 名/状态章/徽标/兵数/发现数/最新时刻", async () => {
    await act(async () => {
      renderAt("/tasks");
    });
    const cards = screen.getAllByTestId("task-card");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveAttribute("data-battle", "battle-1");
    // 名/当代 goal/兵数/发现数如实
    expect(screen.getAllByTestId("task-name")[0]).toHaveTextContent(
      "authorized-range.local",
    );
    expect(screen.getAllByTestId("task-goal")[0]).toHaveTextContent("G-r18");
    expect(screen.getAllByTestId("task-soldiers")[0]).toHaveTextContent("6");
    expect(screen.getAllByTestId("task-findings")[0]).toHaveTextContent("76");
    // 最新时刻: 显 HH:MM:SS,title 带全 ts
    const latest = screen.getAllByTestId("task-latest")[0];
    expect(latest).toHaveTextContent("13:31:00");
    expect(latest).toHaveAttribute("title", "2026-10-14T13:31:00Z");
    // 徽标点: 色=badge,title=仗名
    const dot = screen.getAllByTestId("battle-dot")[0];
    expect(dot).toHaveAttribute("title", "battle-1");
    expect(dot).toHaveStyle({ backgroundColor: "hsl(284, 70%, 60%)" });
  });

  it("状态章: 执行中绿(data-running=true),其余中性(data-running=false)", async () => {
    await act(async () => {
      renderAt("/tasks");
    });
    const chips = screen.getAllByTestId("task-status");
    expect(chips[0]).toHaveTextContent("执行中");
    expect(chips[0]).toHaveAttribute("data-running", "true");
    expect(chips[0].className).toContain("text-ok");
    expect(chips[1]).toHaveTextContent("复测");
    expect(chips[1]).toHaveAttribute("data-running", "false");
    expect(chips[1].className).not.toContain("text-ok");
  });

  it("点仗卡进详情深链 /tasks/:id", async () => {
    await act(async () => {
      renderAt("/tasks");
    });
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("task-card")[1]);
    });
    expect(screen.getByTestId("probe-detail")).toBeInTheDocument();
  });

  it("10s 轮询翻新状态如实(复测→执行中章翻绿)", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch([
        { battles: [B1, B2] },
        { battles: [B1, { ...B2, status: "执行中", running: true }] },
      ]),
    );
    await act(async () => {
      renderAt("/tasks");
    });
    expect(screen.getAllByTestId("task-status")[1]).toHaveTextContent("复测");
    await act(async () => {
      vi.advanceTimersByTime(10000);
    });
    const chip = screen.getAllByTestId("task-status")[1];
    expect(chip).toHaveTextContent("执行中");
    expect(chip).toHaveAttribute("data-running", "true");
  });

  it("空态: 零仗诚实文案,不造卡", async () => {
    vi.stubGlobal("fetch", makeFetch([{ battles: [] }]));
    await act(async () => {
      renderAt("/tasks");
    });
    expect(screen.getByTestId("tasks-empty")).toBeInTheDocument();
    expect(screen.queryByTestId("task-card")).toBeNull();
  });

  it("拉取失败红条(role=alert)+行内重试恢复", async () => {
    const queue: unknown[] = [{ reject: true }, { battles: [B1, B2] }];
    vi.stubGlobal("fetch", makeFetch(queue));
    await act(async () => {
      renderAt("/tasks");
    });
    const bar = screen.getByTestId("tasks-error");
    expect(bar).toHaveAttribute("role", "alert");
    await act(async () => {
      fireEvent.click(screen.getByTestId("tasks-retry"));
    });
    expect(screen.queryByTestId("tasks-error")).toBeNull();
    expect(screen.getAllByTestId("task-card")).toHaveLength(2);
  });
});
