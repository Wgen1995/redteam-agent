import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import ChatPage from "./chat";

/**
 * T5 指挥流页测试(mock api,先红后绿):
 * 首载渲染行 / 1s 增量轮询按 key 去重+新行淡入 / before_key 翻页 /
 * 断线黄条自动恢复 / 仗过滤 chips / 战况板三格 / 战况板失败静默空态 /
 * 输入常活(T6 接线提示)。
 */

interface Row {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

const R1: Row = {
  key: "k1", ts: "2026-10-14T11:00:00Z", kind: "add-goal",
  detail: "add-goal G-demo", battle: "battle-1", badge: "hsl(284, 70%, 60%)",
};
const R2: Row = {
  key: "k2", ts: "2026-10-14T12:00:00Z", kind: "http-get",
  detail: "scan http://x/a", battle: "battle-2", badge: "hsl(3, 70%, 60%)",
};
const R3: Row = {
  key: "k3", ts: "2026-10-14T13:00:00Z", kind: "add-finding",
  detail: "finding FD-1", battle: "battle-1", badge: "hsl(284, 70%, 60%)",
};
const R4: Row = {
  key: "k4", ts: "2026-10-14T14:00:00Z", kind: "replay",
  detail: "replay:EV-1:VERIFIED", battle: "battle-2", badge: "hsl(3, 70%, 60%)",
};
const R0A: Row = {
  key: "k0a", ts: "2026-10-14T09:00:00Z", kind: "note",
  detail: "older row a", battle: "battle-1", badge: "hsl(284, 70%, 60%)",
};
const R0B: Row = {
  key: "k0b", ts: "2026-10-14T08:00:00Z", kind: "note",
  detail: "older row b", battle: "battle-2", badge: "hsl(3, 70%, 60%)",
};

const WARBOARD = {
  soldiers: [
    { corps: "recon", intent: "live-scan", status: "active",
      heartbeat_ts: null, tokens: 100, battle: "battle-2", badge: "hsl(3, 70%, 60%)" },
  ],
  findings_latest: [
    { id: "FD-1", sev: "高", where: "AST-1", title: "finding FD-1",
      verified: true, replay_state: "已验", ts: "2026-10-14T13:00:00Z",
      battle: "battle-1", badge: "hsl(284, 70%, 60%)" },
  ],
  approvals: [
    { id: "a1", event: "http-get http://x/a", risk_line: null,
      timeout_policy: "待审挂起超 30 分钟", ts: "2026-10-14T12:00:00Z",
      battle: "battle-2", badge: "hsl(3, 70%, 60%)" },
  ],
};

type Resp = { ok: boolean; status: number; json: () => Promise<unknown> };

function resp(body: unknown): Resp {
  return { ok: true, status: 200, json: async () => body };
}

/** 按路径前缀分发的 fetch mock;队列为空时重复末项;reject 项抛错。 */
function makeFetch(routes: Record<string, unknown[]>) {
  const last: Record<string, unknown> = {};
  const calls: string[] = [];
  const fn = vi.fn((input: RequestInfo | URL): Promise<Resp> => {
    const url = String(input);
    calls.push(url);
    for (const [frag, queue] of Object.entries(routes)) {
      if (!url.includes(frag)) continue;
      const item = queue.length > 1 ? queue.shift() : queue[0];
      last[frag] = item;
      if (item && typeof item === "object" && "reject" in item) {
        return Promise.reject(new Error("net down"));
      }
      return Promise.resolve(resp(item));
    }
    return Promise.reject(new Error("no route: " + url));
  });
  return Object.assign(fn, { calls });
}

function firstPage(rows: Row[]) {
  return { rows, next_cursor: "CUR0" };
}

describe("指挥台 T5(中央流+战况板)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", makeFetch({
      "/api/chat/stream": [firstPage([R3, R2, R1])],
      "/api/chat/warboard": [WARBOARD],
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("首载渲染行: 尾窗行+仗徽标点+过滤 chips(全部/各仗)", async () => {
    await act(async () => {
      render(<ChatPage />);
    });
    expect(screen.getAllByTestId("chat-row")).toHaveLength(3);
    const stream = screen.getByTestId("chat-stream");
    // T7 时刻卡: 一级人话(词表),未知 kind 兜底 [kind] 原样
    expect(within(stream).getAllByTestId("moment-line")).toHaveLength(3);
    expect(within(screen.getByTestId("row-k1")).getByText("作战目标立卡 G-demo")).toBeInTheDocument();
    expect(within(screen.getByTestId("row-k2")).getByText("[http-get] scan http://x/a")).toBeInTheDocument();
    // 每行带 battle 徽标点(色=badge,title=仗名;战况板内另有,故圈流面)
    const dots = within(screen.getByTestId("chat-stream")).getAllByTestId("battle-dot");
    expect(dots).toHaveLength(3);
    expect(dots[0]).toHaveAttribute("title", "battle-1");
    expect(dots[0]).toHaveStyle({ backgroundColor: "hsl(284, 70%, 60%)" });
    // chips: 全部+两仗
    expect(screen.getByTestId("chip-all")).toHaveTextContent("全部");
    expect(screen.getByTestId("chip-battle-1")).toHaveTextContent("battle-1");
    expect(screen.getByTestId("chip-battle-2")).toHaveTextContent("battle-2");
  });

  it("1s 尾轮询增量: 按 key 去重追加,新行带淡入标记", async () => {
    const fetchMock = makeFetch({
      "/api/chat/stream": [firstPage([R3, R2, R1]), { rows: [R4, R3, R2, R1], next_cursor: "CUR0" }],
      "/api/chat/warboard": [WARBOARD],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ChatPage />);
    });
    expect(screen.getAllByTestId("chat-row")).toHaveLength(3);
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });
    // 重叠 3 行被去重,仅追加 k4;共 4 行,k4 带淡入类
    const rows = screen.getAllByTestId("chat-row");
    expect(rows).toHaveLength(4);
    const fresh = screen.getByTestId("row-k4");
    expect(fresh.className).toContain("row-fade");
    expect(screen.getByTestId("row-k3").className).not.toContain("row-fade");
    // T7: 一级人话(词表),原始行进二级
    expect(within(fresh).getByText("机器复放验真 EV-1 已验")).toBeInTheDocument();
  });

  it("上滑翻页: 加载更早带 before_key,旧行前插无重复", async () => {
    const fetchMock = makeFetch({
      "/api/chat/stream": [
        firstPage([R3, R2, R1]),
        { rows: [R0A, R0B], next_cursor: null },
      ],
      "/api/chat/warboard": [WARBOARD],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ChatPage />);
    });
    const older = screen.getByTestId("load-older");
    expect(older).toBeEnabled();
    await act(async () => {
      fireEvent.click(older);
    });
    expect(fetchMock.calls.some((u) => u.includes("before_key=CUR0"))).toBe(true);
    const rows = screen.getAllByTestId("chat-row");
    expect(rows).toHaveLength(5);          // 3+2,无重复
    // 旧→新渲染: 最旧行在最上
    expect(rows[0]).toHaveAttribute("data-key", "k0b");
    expect(rows[4]).toHaveAttribute("data-key", "k3");
    // 游标尽 → 按钮进「已到最早」不可再翻
    expect(screen.getByTestId("load-older")).toBeDisabled();
  });

  it("断线黄条: 失败显示连接中断,恢复自动撤", async () => {
    const fetchMock = makeFetch({
      "/api/chat/stream": [{ reject: true }, firstPage([R3, R2, R1])],
      "/api/chat/warboard": [WARBOARD],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ChatPage />);
    });
    const banner = screen.getByRole("alert");
    expect(banner).toHaveTextContent("连接中断,重连中");
    // 1s 后下一轮成功 → 黄条撤,行照常渲染
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("chat-row")).toHaveLength(3);
  });

  it("仗过滤: 点选 battle-2 仅显该仗,全部恢复", async () => {
    await act(async () => {
      render(<ChatPage />);
    });
    fireEvent.click(screen.getByTestId("chip-battle-2"));
    let rows = screen.getAllByTestId("chat-row");
    expect(rows).toHaveLength(1);
    expect(rows[0]).toHaveAttribute("data-key", "k2");
    fireEvent.click(screen.getByTestId("chip-all"));
    rows = screen.getAllByTestId("chat-row");
    expect(rows).toHaveLength(3);
  });

  it("T7 两级播报: 一级人话,原 raw 行仅留「原文」二级(kind 着色分 kind)", async () => {
    await act(async () => {
      render(<ChatPage />);
    });
    // 已知 kind: 一级=人话,原始 detail 不在一级
    const row = screen.getByTestId("row-k3");
    expect(within(row).getByText("新发现 FD-1")).toBeInTheDocument();
    expect(within(row).queryByText("finding FD-1")).not.toBeInTheDocument();
    expect(row.className).toContain("text-dang"); // 发现=红
    // 点开二级: 原样 detail/kind/key/battle,透明不藏
    fireEvent.click(within(row).getByTestId("moment-toggle"));
    const raw = within(row).getByTestId("moment-raw");
    expect(raw).toHaveTextContent("finding FD-1");
    expect(raw).toHaveTextContent("kind: add-finding");
    expect(raw).toHaveTextContent("key: k3");
    expect(raw).toHaveTextContent("battle: battle-1");
    // 未知 kind: 一级兜底 [kind] detail 原样
    expect(within(screen.getByTestId("row-k2")).getByText("[http-get] scan http://x/a")).toBeInTheDocument();
  });

  it("战况板三格: 在跑士兵/最新发现/待审批,数据来自 /api/chat/warboard", async () => {
    await act(async () => {
      render(<ChatPage />);
    });
    const board = screen.getByTestId("warboard");
    const soldiers = within(board).getByTestId("wb-soldiers");
    expect(within(soldiers).getByText(/live-scan/)).toBeInTheDocument();
    const findings = within(board).getByTestId("wb-findings");
    expect(within(findings).getByText(/finding FD-1/)).toBeInTheDocument();
    expect(within(findings).getByText("已验")).toBeInTheDocument();
    const approvals = within(board).getByTestId("wb-approvals");
    expect(within(approvals).getByText("http-get http://x/a")).toBeInTheDocument();
  });

  it("战况板失败: 静默空态不造假", async () => {
    vi.stubGlobal("fetch", makeFetch({
      "/api/chat/stream": [firstPage([R3, R2, R1])],
      "/api/chat/warboard": [{ reject: true }],
    }));
    await act(async () => {
      render(<ChatPage />);
    });
    expect(screen.getByTestId("wb-soldiers-empty")).toBeInTheDocument();
    expect(screen.getByTestId("wb-findings-empty")).toBeInTheDocument();
    expect(screen.getByTestId("wb-approvals-empty")).toBeInTheDocument();
    expect(screen.queryByText(/live-scan/)).not.toBeInTheDocument();
    // 流不受战况板失败影响
    expect(screen.getAllByTestId("chat-row")).toHaveLength(3);
  });

  it("输入框常活: 发送即 POST /api/chat/say(带原文),解析中行内提示", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R3, R2, R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "chat", reply: "已收到。" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => {
      render(<ChatPage />);
    });
    const input = screen.getByTestId("chat-input");
    expect(input).toBeEnabled();
    await act(async () => {
      fireEvent.change(input, { target: { value: "扫一下 demo.local" } });
      fireEvent.submit(input.closest("form")!);
    });
    const sayCall = fetchMock.calls.find((c) => c.url.includes("/api/chat/say"));
    expect(sayCall?.method).toBe("POST");
    expect(sayCall?.body).toEqual({ text: "扫一下 demo.local" });
  });
});

// ---------------------------------------------------------------------------
// T6 说话开仗: 输入接 say(意图解析→确认卡→confirm 双钮;失败红条重试)。
// ---------------------------------------------------------------------------

const CARD = {
  kind: "confirm-ignite", id: "c1", target: "demo.example.com",
  scope: ["*.demo.example.com", "只读探测"], budget: "50万 tokens,4 小时",
  auth_notice: "确认开打仅按 dry-run 演练(P0);真点火须授权书在位且预算过仲裁。",
};

const IGNITED = {
  ok: true, cancelled: false, ignited: true, dry_run: true, battle: 4,
  note: "已按 dry-run 点火演练(战号 battle-4,零落账);真点火后续舰接线",
  bridge: { ok: true, dry_run: true, battle: 4, chain: [], note: "P0 dry-run 演练" },
};

const CANCELLED = { ok: true, cancelled: true, note: "已取消,目标保留(卡作废,可重新发起)" };

type Call = { url: string; method: string; body: unknown };

/** GET/POST 混合 fetch mock: POST 带体捕获;队列空重复末项;{reject}|{status,json} 特例。 */
function makeFlowFetch(routes: Record<string, unknown[]>) {
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
      return Promise.resolve(resp(item));
    }
    return Promise.reject(new Error("no route: " + url));
  });
  return Object.assign(fn, { calls });
}

async function submitSay(text: string) {
  const input = screen.getByTestId("chat-input");
  await act(async () => {
    fireEvent.change(input, { target: { value: text } });
    fireEvent.submit(input.closest("form")!);
  });
}

describe("指挥台 T6(说话开仗)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "confirm", card: CARD }],
      "/api/chat/confirm": [IGNITED],
    }));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("解析中态: 发送后行内『指挥→AI 解析中』,回卡即撤", async () => {
    let resolveSay!: (v: Resp) => void;
    const pending = new Promise<Resp>((res) => { resolveSay = res; });
    const fetchMock = vi.fn((input: RequestInfo | URL): Promise<Resp> => {
      const url = String(input);
      if (url.includes("/api/chat/say")) return pending;
      if (url.includes("/api/chat/stream")) return Promise.resolve(resp(firstPage([R1])));
      if (url.includes("/api/chat/warboard")) return Promise.resolve(resp(WARBOARD));
      return Promise.reject(new Error("no route: " + url));
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("对 demo.example.com 开仗,只读,50万 tokens");
    expect(screen.getByTestId("say-parsing")).toHaveTextContent("指挥→AI 解析中");
    await act(async () => {
      resolveSay(resp({ status: "confirm", card: CARD }));
    });
    expect(screen.queryByTestId("say-parsing")).not.toBeInTheDocument();
    expect(screen.getByTestId("say-card")).toBeInTheDocument();
  });

  it("确认卡渲染: kind 着色+目标/范围/预算三行+授权一句+双钮", async () => {
    await act(async () => { render(<ChatPage />); });
    await submitSay("对 demo.example.com 开仗,只读,50万 tokens");
    const card = screen.getByTestId("say-card");
    expect(card).toHaveTextContent("confirm-ignite");
    expect(card.className).toContain("border-acc");        // kind 着色
    expect(card).toHaveTextContent("demo.example.com");
    expect(card).toHaveTextContent("*.demo.example.com");
    expect(card).toHaveTextContent("50万 tokens,4 小时");
    expect(card).toHaveTextContent("授权书");
    expect(screen.getByTestId("say-confirm")).toHaveTextContent("确认开打");
    expect(screen.getByTestId("say-cancel")).toHaveTextContent("取消");
  });

  it("双钮流·确认: POST confirm(approved:true)→点火回执气泡,卡撤", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "confirm", card: CARD }],
      "/api/chat/confirm": [IGNITED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("对 demo.example.com 开仗");
    fireEvent.click(screen.getByTestId("say-confirm"));
    await act(async () => { await Promise.resolve(); });
    const c = fetchMock.calls.find((x) => x.url.includes("/api/chat/confirm"));
    expect(c?.method).toBe("POST");
    expect(c?.body).toEqual({ id: "c1", approved: true });
    expect(screen.queryByTestId("say-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("say-result")).toHaveTextContent("battle-4");
    expect(screen.getByTestId("say-result")).toHaveTextContent("dry-run");
  });

  it("双钮流·取消: POST confirm(approved:false)→『已取消,目标保留』气泡", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "confirm", card: CARD }],
      "/api/chat/confirm": [CANCELLED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("对 demo.example.com 开仗");
    fireEvent.click(screen.getByTestId("say-cancel"));
    await act(async () => { await Promise.resolve(); });
    const c = fetchMock.calls.find((x) => x.url.includes("/api/chat/confirm"));
    expect(c?.body).toEqual({ id: "c1", approved: false });
    expect(screen.queryByTestId("say-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("say-result")).toHaveTextContent("已取消");
    expect(screen.getByTestId("say-result")).toHaveTextContent("目标保留");
  });

  it("失败红条: 502 错误文案不吞+行内重试成功转确认卡", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [
        { httpStatus: 502, json: { error: "模型链全败,意图解析不可用: llm-chain-exhausted" } },
        { status: "confirm", card: CARD },
      ],
      "/api/chat/confirm": [IGNITED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("对 demo.example.com 开仗");
    const bar = screen.getByTestId("say-error");
    expect(bar).toHaveAttribute("role", "alert");
    expect(bar).toHaveTextContent("模型链全败");          // 服务器原文,不吞错
    await act(async () => {
      fireEvent.click(screen.getByTestId("say-retry"));
    });
    expect(screen.queryByTestId("say-error")).not.toBeInTheDocument();
    expect(screen.getByTestId("say-card")).toBeInTheDocument();
  });

  it("闲聊直回: status=chat 气泡显回话,无确认卡无双钮", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "chat", reply: "已收到。这句未识别为开仗指令——说清目标(可选范围/预算)即可开仗。" }],
      "/api/chat/confirm": [IGNITED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("今天天气如何");
    expect(screen.getByTestId("say-chat")).toHaveTextContent("未识别为开仗指令");
    expect(screen.queryByTestId("say-card")).not.toBeInTheDocument();
    expect(screen.queryByTestId("say-confirm")).not.toBeInTheDocument();
    expect(screen.queryByTestId("say-cancel")).not.toBeInTheDocument();
  });

  it("缺项问询: status=ask 问回去,不产卡", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "ask", questions: ["预算给多少(tokens/时长)?"], intent: { target: "demo.example.com", scope: [], budget_note: "" } }],
      "/api/chat/confirm": [IGNITED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await submitSay("扫一下 demo.example.com");
    expect(screen.getByTestId("say-ask")).toHaveTextContent("预算给多少");
    expect(screen.queryByTestId("say-card")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// T8 内联审批: warboard 待审→流顶审批卡组(战况板待审批数=入口);
// 批/拒→POST /api/chat/approve→卡转结果态;warboard 轮询消项后卡自然撤。
// ---------------------------------------------------------------------------

const WARBOARD_EMPTY_AP = {
  soldiers: WARBOARD.soldiers,
  findings_latest: WARBOARD.findings_latest,
  approvals: [],
};

describe("指挥台 T8(内联审批)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("流顶审批卡组: warboard 待审出卡(命令原文),且在流容器之前", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/say": [{ status: "chat", reply: "已收到。" }],
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0001" }],
    }));
    await act(async () => { render(<ChatPage />); });
    const deck = screen.getByTestId("approval-deck");
    const card = within(deck).getByTestId("approval-card");
    expect(card).toHaveTextContent("http-get http://x/a");   // 命令原文
    expect(within(card).getByTestId("approval-approve")).toBeInTheDocument();
    // 卡组在流顶: deck 先于流容器出现于 DOM
    const stream = screen.getByTestId("chat-stream");
    const rel = deck.compareDocumentPosition(stream);
    expect(rel & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("战况板待审批格=入口: 点标题收起/展开卡组", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0001" }],
    }));
    await act(async () => { render(<ChatPage />); });
    expect(screen.getByTestId("approval-card")).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(screen.getByTestId("wb-approvals-entry"));
    });
    expect(screen.queryByTestId("approval-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("approval-deck")).toBeInTheDocument(); // 组头还在
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-deck-toggle"));
    });
    expect(screen.getByTestId("approval-card")).toBeInTheDocument();
  });

  it("批一次: POST approve 带仗名+命令哈希,卡转绿已批准", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0009", decision: "approve" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-approve"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/approve"));
    expect(call?.method).toBe("POST");
    expect(call?.body).toEqual({
      battle: "battle-2", command_hash: "a1", decision: "approve",
    });
    const done = screen.getByTestId("approval-done");
    expect(done).toHaveTextContent("已批准");
    expect(done).toHaveTextContent("AP-1-0009");
  });

  it("决后轮询消项: warboard 下轮无该待审→卡自然撤(零待审=组不显)", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD, WARBOARD_EMPTY_AP],
      "/api/chat/approve": [{ ok: true, approval_id: "AP-1-0010", decision: "approve" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-approve"));
    });
    expect(screen.getByTestId("approval-done")).toBeInTheDocument();  // 决后仍显结果
    await act(async () => {
      vi.advanceTimersByTime(10000);                                  // 下一轮战况板
    });
    expect(screen.queryByTestId("approval-card")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approval-deck")).not.toBeInTheDocument();
  });

  it("审批失败红条: 服务器原文不吞,重试可再提交", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/approve": [
        { httpStatus: 502, json: { error: "审批桥失败(rc=2): 引擎拒收审批" } },
        { ok: true, approval_id: "AP-1-0011", decision: "reject" },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-reject"));
    });
    const bar = screen.getByTestId("approval-error");
    expect(bar).toHaveAttribute("role", "alert");
    expect(bar).toHaveTextContent("引擎拒收审批");
    await act(async () => {
      fireEvent.click(screen.getByTestId("approval-retry"));
    });
    expect(screen.getByTestId("approval-done")).toHaveTextContent("已拒绝");
  });

  it("零待审: warboard approvals 空 → 无卡组不占位", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD_EMPTY_AP],
    }));
    await act(async () => { render(<ChatPage />); });
    expect(screen.queryByTestId("approval-deck")).not.toBeInTheDocument();
    expect(screen.getByTestId("wb-approvals-empty")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// T9 发现时刻卡: 流中 add-finding/supersede-finding 行与 /api/chat/findings
// 配对(30s 轮询拉取,仗优先配对)→ 升级发现卡;配不到回退 T7 原卡。
// ---------------------------------------------------------------------------

const FD1 = {   // battle-1 已验(C2)
  id: "FD-1", title: "finding FD-1", severity: "C2", where: "AST-1",
  verified: true, replay_state: "已验", evidence: ["EV-1"],
  battle: "battle-1", badge: "hsl(284, 70%, 60%)", ts: "2026-10-14T13:00:00Z",
};
const FD1_PENDING = {   // 30s 后复验中(徽须如实翻灰,不滞留旧绿)
  ...FD1, verified: false, replay_state: "复验中",
};
const FD9 = {   // battle-2 复验中(C1)
  id: "FD-9", title: "finding FD-9", severity: "C1", where: null,
  verified: false, replay_state: "复验中", evidence: [],
  battle: "battle-2", badge: "hsl(3, 70%, 60%)", ts: "2026-10-14T12:30:00Z",
};
const R_SUPER: Row = {   // supersede 行(箭头目标 FD-9)
  key: "k9", ts: "2026-10-14T12:30:30Z", kind: "supersede-finding",
  detail: "supersede-finding FD-8->FD-9", battle: "battle-2", badge: "hsl(3, 70%, 60%)",
};
const R_MISS: Row = {   // findings 里配不到的发现行
  key: "k5", ts: "2026-10-14T10:00:00Z", kind: "add-finding",
  detail: "add-finding FD-404", battle: "battle-1", badge: "hsl(284, 70%, 60%)",
};

/** 流行 li 定位(键=服务端行 key;升级后卡根 testid 变 finding-card)。 */
function rowOf(key: string): HTMLElement {
  const el = document.querySelector('[data-testid="chat-row"][data-key="' + key + '"]');
  if (!el) throw new Error("chat-row not found: " + key);
  return el as HTMLElement;
}

describe("指挥台 T9(发现时刻卡)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("配对升级: add-finding/supersede-finding 行升发现卡(发现号+标题+四色章+三态徽)", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R_SUPER, R3, R2, R_MISS, R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/findings": [[FD1, FD9]],
    }));
    await act(async () => { render(<ChatPage />); });
    // R3(add-finding FD-1)→ 发现卡: 号+标题+严重度章+验真徽(绿·机器已验)
    const c1 = rowOf("k3").firstElementChild as HTMLElement;
    expect(c1).toHaveAttribute("data-testid", "finding-card");
    expect(c1).toHaveAttribute("data-fd", "FD-1");
    expect(within(c1).getByTestId("finding-title")).toHaveTextContent("finding FD-1");
    const sev = within(c1).getByTestId("sev-chip");
    expect(sev).toHaveAttribute("data-sev", "high");       // C2→高
    expect(sev).toHaveTextContent("C2");
    const ver = within(c1).getByTestId("verify-chip");
    expect(ver).toHaveAttribute("data-state", "verified");
    expect(ver).toHaveTextContent("机器已验");
    // R_SUPER(supersede-finding FD-8->FD-9)→ 配箭头目标 FD-9+更替来源注记
    const c9 = rowOf("k9").firstElementChild as HTMLElement;
    expect(c9).toHaveAttribute("data-testid", "finding-card");
    expect(c9).toHaveAttribute("data-fd", "FD-9");
    expect(within(c9).getByText(/更替自 FD-8/)).toBeInTheDocument();
    const ver9 = within(c9).getByTestId("verify-chip");
    expect(ver9).toHaveAttribute("data-state", "pending");  // 复验中→灰·待机器复验
    expect(ver9).toHaveTextContent("待机器复验");
    // 二级: 原文+证据袋引用(有则显)
    fireEvent.click(within(c1).getByTestId("finding-toggle"));
    expect(within(c1).getByTestId("finding-raw")).toHaveTextContent("finding FD-1");
    expect(within(c1).getByTestId("finding-evidence")).toHaveTextContent("EV-1");
  });

  it("配不到回退: findings 无该发现号 → T7 原卡不硬凑", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R_MISS, R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/findings": [[FD1]],
    }));
    await act(async () => { render(<ChatPage />); });
    const miss = rowOf("k5").firstElementChild as HTMLElement;
    expect(miss).toHaveAttribute("data-testid", "row-k5");   // 原卡根=testid 行键
    expect(within(miss).getByTestId("moment-line")).toHaveTextContent("新发现 FD-404");
    expect(within(miss).queryByTestId("sev-chip")).not.toBeInTheDocument();
    expect(within(miss).queryByTestId("verify-chip")).not.toBeInTheDocument();
  });

  it("findings 拉取失败: 静默回退原卡,流不受影响", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R3, R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/findings": [{ reject: true }],
    }));
    await act(async () => { render(<ChatPage />); });
    expect(screen.queryByTestId("finding-card")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("moment-line").length).toBe(2);
    expect(within(screen.getByTestId("row-k3")).getByText("新发现 FD-1")).toBeInTheDocument();
  });

  it("30s 轮询刷新: 验真态翻新如实(绿→灰不滞留),挂载首拉+30s 一拉", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R3, R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/findings": [[FD1], [FD1_PENDING]],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    expect(screen.getByTestId("verify-chip")).toHaveAttribute("data-state", "verified");
    await act(async () => { vi.advanceTimersByTime(30000); });
    const calls = fetchMock.calls.filter((c) => c.url.includes("/api/chat/findings")).length;
    expect(calls).toBe(2);                                   // 挂载首拉+30s 一拉
    expect(screen.getByTestId("verify-chip")).toHaveAttribute("data-state", "pending");
    expect(screen.getByTestId("verify-chip")).toHaveTextContent("待机器复验");
  });

  it("仗优先配对: 同号异仗取本仗发现(兜底才全局)", async () => {
    const fdOther = { ...FD1, battle: "battle-2", title: "battle-2 的同名发现" };
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R3, R1])],           // R3 在 battle-1
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/findings": [[fdOther, { ...FD1, title: "battle-1 本仗发现" }]],
    }));
    await act(async () => { render(<ChatPage />); });
    expect(within(screen.getByTestId("finding-card")).getByTestId("finding-title"))
      .toHaveTextContent("battle-1 本仗发现");
  });
});

// ---------------------------------------------------------------------------
// T10 插话与转向: 流顶在跑仗条(显隐/插话带仗/全停确认流/失败红条)。
// 数据面=GET /api/chat/running(执行中口径);发送=POST /api/chat/steer|halt。
// ---------------------------------------------------------------------------

const RUNNING = {
  battles: [
    { battle: "battle-2", badge: "hsl(3, 70%, 60%)", detail: "已点火（runner 未完跑）" },
  ],
};
const RUNNING_EMPTY = { battles: [] };
const STEERED = {
  ok: true, battle: "battle-2", text: "跳过 10.2.0.9", intent: "",
  warriors: ["w1"], timeline_row: 6,
  note: "插话已入链（战士 w1）；回执时刻经流自然来",
};
const HALTED = {
  ok: true, battle: "battle-2", reason: "预算超限", stopped: ["w1"],
  timeline_row: 8, note: "全停已入链（w1）；停令时刻经流自然来",
};

async function typeDraft(text: string) {
  const input = screen.getByTestId("chat-input");
  await act(async () => {
    fireEvent.change(input, { target: { value: text } });
  });
}

describe("指挥台 T10(插话与转向)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("在跑仗条显: 执行中仗名+徽标+插话/全停两小钮(输入框上方)", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
    }));
    await act(async () => { render(<ChatPage />); });
    const bar = screen.getByTestId("running-bar");
    const row = within(bar).getByTestId("running-battle-2");
    expect(row).toHaveTextContent("battle-2");
    const dot = within(row).getByTestId("battle-dot");
    expect(dot).toHaveAttribute("title", "battle-2");
    expect(dot).toHaveStyle({ backgroundColor: "hsl(3, 70%, 60%)" });
    expect(within(row).getByTestId("steer-battle-2")).toHaveTextContent("插话");
    expect(within(row).getByTestId("halt-battle-2")).toHaveTextContent("全停");
    // 条在输入框上方: bar 先于 form 出现于 DOM
    const form = screen.getByTestId("chat-input").closest("form")!;
    const rel = bar.compareDocumentPosition(form);
    expect(rel & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("在跑仗条隐: 无在跑仗=条隐藏不占位", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING_EMPTY],
    }));
    await act(async () => { render(<ChatPage />); });
    expect(screen.queryByTestId("running-bar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("steer-battle-2")).not.toBeInTheDocument();
  });

  it("插话: 输入框内容以 steer 发送(带仗标),回执气泡显,输入清空", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/steer": [STEERED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await typeDraft("跳过 10.2.0.9,重点 10.2.0.7");
    await act(async () => {
      fireEvent.click(screen.getByTestId("steer-battle-2"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/steer"));
    expect(call?.method).toBe("POST");
    expect(call?.body).toEqual({ battle: "battle-2", text: "跳过 10.2.0.9,重点 10.2.0.7" });
    expect(screen.getByTestId("deck-result")).toHaveTextContent("插话已入链");
    expect(screen.getByTestId("deck-result")).toHaveTextContent("经流自然来");
    expect(screen.getByTestId("chat-input")).toHaveValue("");     // 输入已消费
  });

  it("插话空输入: 钮禁用不发请求", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/steer": [STEERED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    expect(screen.getByTestId("steer-battle-2")).toBeDisabled();
  });

  it("全停确认流: 确认小卡(原因可选)→halt 带 reason;取消不发", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/halt": [HALTED],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-battle-2"));
    });
    const card = screen.getByTestId("halt-confirm");
    expect(card).toHaveTextContent("battle-2");                 // 卡上带仗
    await act(async () => {
      fireEvent.change(screen.getByTestId("halt-reason"), { target: { value: "预算超限" } });
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-confirm-ok"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/halt"));
    expect(call?.method).toBe("POST");
    expect(call?.body).toEqual({ battle: "battle-2", reason: "预算超限" });
    expect(screen.getByTestId("deck-result")).toHaveTextContent("全停已入链");
    // 取消路径: 另开一仗确认后取消,零 halt 请求
    const fetchMock2 = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/halt": [HALTED],
    });
    vi.stubGlobal("fetch", fetchMock2);
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-battle-2"));
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-confirm-cancel"));
    });
    expect(fetchMock2.calls.some((c) => c.url.includes("/api/chat/halt"))).toBe(false);
    expect(screen.queryByTestId("halt-confirm")).not.toBeInTheDocument();
  });

  it("全停不带原因也可确认: body 无 reason 字段", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/halt": [{ ...HALTED, reason: "指挥台全停" }],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-battle-2"));
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("halt-confirm-ok"));
    });
    const call = fetchMock.calls.find((c) => c.url.includes("/api/chat/halt"));
    expect(call?.body).toEqual({ battle: "battle-2" });         // 原因可选=不带字段
  });

  it("失败红条: steer 502 服务器原文不吞+行内重试转绿", async () => {
    const fetchMock = makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/steer": [
        { httpStatus: 502, json: { error: "桥失败（rc=2）: 战目录无 goal 代目录: battle-2" } },
        STEERED,
      ],
    });
    vi.stubGlobal("fetch", fetchMock);
    await act(async () => { render(<ChatPage />); });
    await typeDraft("跳过 10.2.0.9");
    await act(async () => {
      fireEvent.click(screen.getByTestId("steer-battle-2"));
    });
    const bar = screen.getByTestId("deck-error");
    expect(bar).toHaveAttribute("role", "alert");
    expect(bar).toHaveTextContent("战目录无 goal 代目录");      // 原文不吞
    await act(async () => {
      fireEvent.click(screen.getByTestId("deck-retry"));
    });
    expect(screen.queryByTestId("deck-error")).not.toBeInTheDocument();
    expect(screen.getByTestId("deck-result")).toHaveTextContent("插话已入链");
  });

  it("say 意图 steer/halt: 分类气泡指路在跑仗条,不产确认卡", async () => {
    vi.stubGlobal("fetch", makeFlowFetch({
      "/api/chat/stream": [firstPage([R1])],
      "/api/chat/warboard": [WARBOARD],
      "/api/chat/running": [RUNNING],
      "/api/chat/say": [{ status: "steer", reply: "已识别为对进行中仗的插话指令——请用流顶在跑仗条的「插话」钮发出。", intent: { target_intent: "跳过 10.2.0.9" } }],
    }));
    await act(async () => { render(<ChatPage />); });
    await submitSay("跳过 10.2.0.9");
    expect(screen.getByTestId("say-chat")).toHaveTextContent("插话指令");
    expect(screen.queryByTestId("say-card")).not.toBeInTheDocument();
  });
});
