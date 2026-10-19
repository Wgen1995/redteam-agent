import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import TaskDetailPage from "./task-detail";

/**
 * T11 任务详情·会话签页测试(mock api,先红后绿):
 * 仗头渲染(名/状态章/徽标/当代 goal/简述) / 会话卡(标签/行数/起止) /
 * 点开组流渲染(复用 MomentCard/FindingCard) / 10s 尾轮询追加 /
 * 翻页加载更早 / 返回列表钮 / 未知仗空态。
 */

interface Session {
  session_key: string;
  label: string;
  rows_n: number;
  first_ts: string;
  last_ts: string;
}

interface Detail {
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
  objective: string;
  sessions: Session[];
}

const DETAIL: Detail = {
  id: "battle-4",
  name: "warrior-target",
  status: "执行中",
  status_detail: "已点火（runner 未完跑）",
  running: true,
  badge: "hsl(172, 70%, 60%)",
  goal: "G-1",
  soldiers_n: 1,
  findings_n: 0,
  latest_ts: "2026-10-14T09:00:45Z",
  objective: "会话签分组演示仗",
  sessions: [
    {
      session_key: "w:w1",
      label: "战士 w1",
      rows_n: 5,
      first_ts: "2026-10-14T09:00:05Z",
      last_ts: "2026-10-14T09:00:40Z",
    },
    {
      session_key: "deck",
      label: "战役本级",
      rows_n: 2,
      first_ts: "2026-10-14T09:00:00Z",
      last_ts: "2026-10-14T09:00:45Z",
    },
  ],
};

interface Row {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

const S1: Row = {
  key: "k1", ts: "2026-10-14T09:00:40Z", kind: "warrior-stop",
  detail: "warrior-stop warrior=w1 reason=demo halt", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};
const S2: Row = {
  key: "k2", ts: "2026-10-14T09:00:30Z", kind: "warrior-steer",
  detail: "warrior-steer target=w1 text=skip 10.2.0.9", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};
const S3: Row = {
  key: "k3", ts: "2026-10-14T09:00:20Z", kind: "http-get",
  detail: "http-get http://10.2.0.7/", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};
const S0: Row = {
  key: "k0", ts: "2026-10-14T09:00:05Z", kind: "warrior-start",
  detail: "warrior-start battle=battle-4 warrior=w1", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};
const SNEW: Row = {
  key: "k9", ts: "2026-10-14T09:01:00Z", kind: "warrior-heartbeat",
  detail: "warrior-heartbeat warrior=w1 intent=INT-4-1", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};

const FINDING = {
  id: "FD-4-1", title: "管理面暴露", severity: "C1", where: "10.2.0.7",
  verified: true, replay_state: "已验", evidence: ["EV-4-1"],
  battle: "battle-4", badge: "hsl(172, 70%, 60%)",
  ts: "2026-10-14T09:00:35Z",
};
const S_FINDING: Row = {
  key: "k5", ts: "2026-10-14T09:00:35Z", kind: "add-finding",
  detail: "add-finding FD-4-1", battle: "battle-4",
  badge: "hsl(172, 70%, 60%)",
};

type Resp = { ok: boolean; status: number; json: () => Promise<unknown> };

function resp(body: unknown, ok = true, status = 200): Resp {
  return { ok, status, json: async () => body };
}

/** 按路径分发的 fetch mock;详情/组流/发现三路;reject 项抛错。 */
function makeFetch(routes: Record<string, unknown[]>) {
  const fn = vi.fn((input: RequestInfo | URL): Promise<Resp> => {
    const url = String(input);
    for (const [frag, queue] of Object.entries(routes)) {
      if (!url.includes(frag)) continue;
      const item = queue.length > 1 ? queue.shift() : queue[0];
      if (item && typeof item === "object" && "reject" in item) {
        return Promise.reject(new Error("net down"));
      }
      if (item && typeof item === "object" && "notFound" in item) {
        return Promise.resolve(resp({ error: "battle 不存在" }, false, 404));
      }
      return Promise.resolve(resp(item));
    }
    return Promise.reject(new Error("no route: " + url));
  });
  return Object.assign(fn, {});
}

/** 壳内路由: /tasks 探针+/tasks/:id 实页。 */
function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/tasks" element={<div data-testid="probe-list">list</div>} />
        <Route path="/tasks/:id" element={<TaskDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("任务详情·会话签 T11", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("仗头渲染: 名/状态章/徽标/当代 goal/简述+返回列表钮", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({ "/api/tasks/battle-4": [DETAIL] }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    expect(screen.getByTestId("task-detail-name")).toHaveTextContent(
      "warrior-target",
    );
    const chip = screen.getByTestId("task-status");
    expect(chip).toHaveTextContent("执行中");
    expect(chip).toHaveAttribute("data-running", "true");
    expect(screen.getByTestId("task-goal")).toHaveTextContent("G-1");
    expect(screen.getByTestId("task-objective")).toHaveTextContent(
      "会话签分组演示仗",
    );
    expect(screen.getByTestId("battle-dot")).toHaveStyle({
      backgroundColor: "hsl(172, 70%, 60%)",
    });
    expect(screen.getByTestId("task-soldiers")).toHaveTextContent("1");
    expect(screen.getByTestId("task-findings")).toHaveTextContent("0");
    expect(screen.getByTestId("back-to-tasks")).toBeInTheDocument();
  });

  it("会话签区: 每战士/意图一会话卡(标签/行数/起止)", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({ "/api/tasks/battle-4": [DETAIL] }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    const cards = screen.getAllByTestId("session-card");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveAttribute("data-key", "w:w1");
    expect(
      within(cards[0]).getByTestId("session-label"),
    ).toHaveTextContent("战士 w1");
    expect(cards[0]).toHaveTextContent("5");
    expect(cards[0]).toHaveTextContent("09:00:05");
    expect(cards[0]).toHaveTextContent("09:00:40");
    expect(
      within(cards[1]).getByTestId("session-label"),
    ).toHaveTextContent("战役本级");
  });

  it("点开会话卡→组流渲染(MomentCard 原卡+发现行升 FindingCard)", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({
        "/api/tasks/battle-4/sessions/": [
          { rows: [S1, S2, S3, S_FINDING], next_cursor: "k3" },
        ],
        "/api/chat/findings": [[FINDING]],
        "/api/tasks/battle-4": [DETAIL],
      }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("session-card")[0]);
    });
    const stream = screen.getByTestId("session-stream");
    expect(within(stream).getAllByTestId("session-row")).toHaveLength(4);
    // 原卡: 未知/词表行经 MomentCard 渲染(steer 留痕可见)
    expect(within(stream).getAllByTestId("moment-line").length).toBeGreaterThanOrEqual(3);
    // 发现行配对升 FindingCard(发现号+严重度章+验真徽)
    const fc = within(stream).getByTestId("finding-card");
    expect(fc).toHaveAttribute("data-fd", "FD-4-1");
    expect(within(fc).getByTestId("sev-chip")).toHaveAttribute(
      "data-sev",
      "critical",
    );
    expect(within(fc).getByTestId("verify-chip")).toHaveAttribute(
      "data-state",
      "verified",
    );
  });

  it("10s 尾轮询: 新行按 key 去重追加", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({
        "/api/tasks/battle-4/sessions/": [
          { rows: [S1, S2], next_cursor: null },
          { rows: [SNEW, S1, S2], next_cursor: null },
        ],
        "/api/chat/findings": [[]],
        "/api/tasks/battle-4": [DETAIL],
      }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("session-card")[0]);
    });
    expect(screen.getAllByTestId("session-row")).toHaveLength(2);
    await act(async () => {
      vi.advanceTimersByTime(10000);
    });
    expect(screen.getAllByTestId("session-row")).toHaveLength(3);
    expect(screen.getByTestId("row-k9")).toBeInTheDocument();
  });

  it("翻页: next_cursor 在→加载更早钮可用,点按前插旧行", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({
        "/api/tasks/battle-4/sessions/": [
          { rows: [S1, S2], next_cursor: "k2" },
          { rows: [S3, S0], next_cursor: null },
        ],
        "/api/chat/findings": [[]],
        "/api/tasks/battle-4": [DETAIL],
      }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    await act(async () => {
      fireEvent.click(screen.getAllByTestId("session-card")[0]);
    });
    const btn = screen.getByTestId("load-older");
    expect(btn).toBeEnabled();
    await act(async () => {
      fireEvent.click(btn);
    });
    expect(screen.getAllByTestId("session-row")).toHaveLength(4);
    // 旧行前插: 首=最老 start 行
    expect(screen.getAllByTestId("session-row")[0]).toContainElement(
      screen.getByTestId("row-k0"),
    );
  });

  it("返回列表钮 → /tasks", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({ "/api/tasks/battle-4": [DETAIL] }),
    );
    await act(async () => {
      renderAt("/tasks/battle-4");
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("back-to-tasks"));
    });
    expect(screen.getByTestId("probe-list")).toBeInTheDocument();
  });

  it("未知仗空态: 404 如实,不造详情", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch({ "/api/tasks": [{ notFound: true }] }),
    );
    await act(async () => {
      renderAt("/tasks/battle-nope");
    });
    expect(screen.getByTestId("task-not-found")).toBeInTheDocument();
    expect(screen.queryByTestId("task-detail")).toBeNull();
    expect(screen.getByTestId("back-to-tasks")).toBeInTheDocument();
  });
});
