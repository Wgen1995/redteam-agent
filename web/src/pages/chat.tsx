import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent, UIEvent } from "react";
import MomentCard from "../components/moment/MomentCard";

/**
 * 指挥台(P0 T5 件B + T7 两级播报): 中央时刻流+右侧战况板。
 *
 * - 中央流: 1s 尾轮询 GET /api/chat/stream,增量按 key 去重追加,新行
 *   淡入;断线顶部黄条「连接中断,重连中…」自动恢复(轮询不停);
 *   上滑触顶自动加载更早(before_key 翻页,另有显式按钮);每行=T7
 *   MomentCard 时刻卡(一级人话=kinds.ts 词表+kind 着色+battle 徽标点,
 *   二级点开原样 detail/kind/key/battle;原 raw 行仅留「原文」二级)。
 * - 顶栏仗过滤 chips(全部/各仗,点选客户端过滤)。
 * - 右侧战况板三格(可收起): 在跑士兵/最新发现/待审批,10s 轮询
 *   /api/chat/warboard;失败静默空态不造假。
 * - 输入框常活(T6 说话开仗): 发送→POST /api/chat/say(行内「指挥→AI
 *   解析中」态)→confirm-ignite 确认卡气泡(kind 着色,目标/范围/预算三行
 *   +授权一句+确认开打/取消双钮);确认→POST /api/chat/confirm,点火时刻
 *   不在本页伪造——真点火经 stream 轮询自然到来,回执气泡只显 dry-run
 *   演练结果;取消→「已取消,目标保留」。失败红条(role=alert)带行内
 *   重试,服务器错误原文透出不吞。
 */

export interface StreamRow {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

export interface StreamDoc {
  rows: StreamRow[];
  next_cursor: string | null;
}

export interface WarboardItem {
  battle: string;
  badge: string;
  [k: string]: unknown;
}

export interface WarboardDoc {
  soldiers: WarboardItem[];
  findings_latest: WarboardItem[];
  approvals: WarboardItem[];
}

/** T6 确认卡(服务端 /api/chat/say confirm 态回体)。 */
export interface ConfirmCard {
  kind: string;
  id: string;
  target: string;
  scope: string[];
  budget: string;
  auth_notice: string;
}

/** 说话开仗交互态机: 解析中→(问询|闲聊|确认卡)→(点火回执|已取消|红条重试)。 */
type SayFlow =
  | { phase: "idle" }
  | { phase: "parsing" }
  | { phase: "ask"; questions: string[] }
  | { phase: "chat"; reply: string }
  | { phase: "confirm"; card: ConfirmCard }
  | { phase: "busy"; card: ConfirmCard; approved: boolean }
  | { phase: "result"; text: string }
  | { phase: "error"; message: string; retry: () => void };

/** POST JSON;失败/坏体也 resolve 成 {ok:false,...},错误文案不吞。 */
async function postJSON(url: string, body: unknown): Promise<{ ok: boolean; status: number; data: unknown }> {
  try {
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      data = null; // 非 JSON 体: 保错误路径可见
    }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return {
      ok: false, status: 0,
      data: { error: "网络失败: " + (e instanceof Error ? e.message : String(e)) },
    };
  }
}

const STREAM_POLL_MS = 1000;
const WARBOARD_POLL_MS = 10000;

/** 拉取+形状校验;失败/坏形状→null(宁缺毋假)。 */
async function fetchJSON<T>(url: string, check: (v: unknown) => T | null): Promise<T | null> {
  try {
    const res = await fetch(url, { credentials: "same-origin" });
    if (!res.ok) return null;
    return check(await res.json());
  } catch {
    return null;
  }
}

function asStreamDoc(v: unknown): StreamDoc | null {
  if (typeof v !== "object" || v === null) return null;
  const d = v as { rows?: unknown; next_cursor?: unknown };
  if (!Array.isArray(d.rows)) return null;
  const rows = d.rows.filter(
    (r): r is StreamRow =>
      typeof r === "object" &&
      r !== null &&
      typeof (r as StreamRow).key === "string" &&
      typeof (r as StreamRow).ts === "string" &&
      typeof (r as StreamRow).kind === "string" &&
      typeof (r as StreamRow).detail === "string" &&
      typeof (r as StreamRow).battle === "string" &&
      typeof (r as StreamRow).badge === "string",
  );
  const cursor = d.next_cursor;
  return {
    rows,
    next_cursor: typeof cursor === "string" ? cursor : null,
  };
}

function asWarboardDoc(v: unknown): WarboardDoc | null {
  if (typeof v !== "object" || v === null) return null;
  const d = v as Record<string, unknown>;
  const list = (x: unknown): WarboardItem[] =>
    Array.isArray(x)
      ? x.filter(
          (i): i is WarboardItem =>
            typeof i === "object" &&
            i !== null &&
            typeof (i as WarboardItem).battle === "string" &&
            typeof (i as WarboardItem).badge === "string",
        )
      : [];
  if (
    !Array.isArray(d.soldiers) ||
    !Array.isArray(d.findings_latest) ||
    !Array.isArray(d.approvals)
  ) {
    return null;
  }
  return {
    soldiers: list(d.soldiers),
    findings_latest: list(d.findings_latest),
    approvals: list(d.approvals),
  };
}

/** 旧→新全序(ts 升,同 ts 以 key 倒——服务端 (ts,key) 双倒的镜像)。 */
function byOrder(a: StreamRow, b: StreamRow): number {
  if (a.ts !== b.ts) return a.ts < b.ts ? -1 : 1;
  if (a.key !== b.key) return a.key > b.key ? -1 : 1;
  return 0;
}

/** 并集去重排序(追加与前插共用)。 */
function mergeRows(existing: StreamRow[], incoming: StreamRow[]): StreamRow[] {
  const map = new Map(existing.map((r) => [r.key, r]));
  for (const r of incoming) if (!map.has(r.key)) map.set(r.key, r);
  return [...map.values()].sort(byOrder);
}

function BattleDot({ battle, badge }: { battle: string; badge: string }) {
  return (
    <span
      data-testid="battle-dot"
      title={battle}
      aria-label={battle}
      className="inline-block size-2 shrink-0 rounded-full"
      style={{ backgroundColor: badge }}
    />
  );
}

function Chip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-testid={label === "全部" ? "chip-all" : "chip-" + label}
      aria-pressed={active}
      onClick={onClick}
      className={
        "rounded-glds-s border px-2.5 py-1 font-mono text-fs-a transition-colors " +
        (active
          ? "border-acc/60 bg-acc-dim text-acc"
          : "border-line-2 bg-bg-raise text-tx4 hover:text-tx2")
      }
    >
      {label}
    </button>
  );
}

/** T6 确认卡气泡: kind 着色+目标/范围/预算三行+授权一句+双钮。 */
function SayConfirmCard({
  card,
  busy,
  onConfirm,
  onCancel,
}: {
  card: ConfirmCard;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div
      data-testid="say-card"
      className="rounded-glds-s border border-acc/60 bg-acc-dim px-3 py-2.5 font-mono text-fs-a leading-6"
    >
      <div className="flex items-center gap-2 text-acc">
        <span className="rounded-glds-s border border-acc/40 px-1.5">{card.kind}</span>
        <span className="text-tx3">待确认——开仗前请核对三行</span>
      </div>
      <ul className="mt-1.5 flex flex-col gap-0.5 text-tx2">
        <li>
          <span className="text-tx4">目标: </span>
          {card.target}
        </li>
        <li>
          <span className="text-tx4">范围: </span>
          {card.scope.length > 0 ? card.scope.join("; ") : "未说明"}
        </li>
        <li>
          <span className="text-tx4">预算: </span>
          {card.budget || "未说明"}
        </li>
      </ul>
      <p className="mt-1 text-warn">{card.auth_notice}</p>
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          data-testid="say-confirm"
          disabled={busy}
          onClick={onConfirm}
          className="rounded-glds-s bg-acc px-3 py-1 font-medium text-acc-on disabled:opacity-50"
        >
          {busy ? "执行中…" : "确认开打"}
        </button>
        <button
          type="button"
          data-testid="say-cancel"
          disabled={busy}
          onClick={onCancel}
          className="rounded-glds-s border border-line-2 px-3 py-1 text-tx3 hover:text-tx1 disabled:opacity-50"
        >
          取消
        </button>
      </div>
    </div>
  );
}

function WbPanel({
  testid,
  title,
  items,
  empty,
}: {
  testid: string;
  title: string;
  items: WarboardItem[];
  empty: string;
}) {
  return (
    <section data-testid={testid} className="border-b border-line px-3 py-2.5">
      <h3 className="mb-1.5 text-fs-a tracking-[1px] text-tx4">
        {title}
        <span className="ml-1.5 font-mono text-tx5">{items.length}</span>
      </h3>
      {items.length === 0 ? (
        <p data-testid={testid + "-empty"} className="text-fs-a text-tx5">
          {empty}
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {items.map((it, i) => (
            <li
              key={i}
              className="flex items-start gap-1.5 rounded-glds-s bg-bg-raise px-2 py-1.5 text-fs-a leading-5 text-tx3"
            >
              <BattleDot battle={it.battle} badge={it.badge} />
              <span className="min-w-0 break-all">
                {"intent" in it ? String(it.intent) + " · " : ""}
                {"title" in it ? String(it.title) : ""}
                {"event" in it ? String(it.event) : ""}
                {"replay_state" in it ? (
                  <span className="ml-1 text-ok">{String(it.replay_state)}</span>
                ) : null}
                {"status" in it ? (
                  <span className="ml-1 text-tx5">{String(it.status)}</span>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ChatPage() {
  const [rows, setRows] = useState<StreamRow[]>([]);
  const [fresh, setFresh] = useState<string[]>([]);
  const [olderCursor, setOlderCursor] = useState<string | null | undefined>(undefined);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [disconnected, setDisconnected] = useState(false);
  const [battleFilter, setBattleFilter] = useState<string | null>(null);
  const [board, setBoard] = useState<WarboardDoc | null>(null);
  const [boardOpen, setBoardOpen] = useState(true);
  const [draft, setDraft] = useState("");
  const [flow, setFlow] = useState<SayFlow>({ phase: "idle" });
  const scrollRef = useRef<HTMLDivElement>(null);
  const nearBottomRef = useRef(true);
  const loadingOlderRef = useRef(false);

  // 1s 尾轮询: 增量按 key 去重追加;失败=断线黄条,轮询不停自动恢复。
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const doc = await fetchJSON("/api/chat/stream", asStreamDoc);
      if (!alive) return;
      if (doc === null) {
        setDisconnected(true);
        return;
      }
      setDisconnected(false);
      setRows((prev) => {
        const known = new Set(prev.map((r) => r.key));
        const added = doc.rows.filter((r) => !known.has(r.key));
        if (added.length > 0) setFresh(added.map((r) => r.key));
        return added.length > 0 ? mergeRows(prev, doc.rows) : prev;
      });
      setOlderCursor((prev) => (prev === undefined ? doc.next_cursor : prev));
    };
    void tick();
    const id = setInterval(tick, STREAM_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // 10s 战况板轮询: 失败静默空态(不造假),流不受影响。
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const doc = await fetchJSON("/api/chat/warboard", asWarboardDoc);
      if (alive && doc !== null) setBoard(doc);
    };
    void tick();
    const id = setInterval(tick, WARBOARD_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // 新行到达且视口贴底时跟随滚到最底。
  useEffect(() => {
    const el = scrollRef.current;
    if (el && nearBottomRef.current && el.scrollHeight > 0) {
      el.scrollTop = el.scrollHeight;
    }
  }, [rows]);

  const loadOlder = useCallback(async () => {
    if (loadingOlderRef.current || !olderCursor) return;
    loadingOlderRef.current = true;
    setLoadingOlder(true);
    const doc = await fetchJSON(
      "/api/chat/stream?before_key=" + encodeURIComponent(olderCursor),
      asStreamDoc,
    );
    loadingOlderRef.current = false;
    setLoadingOlder(false);
    if (doc === null) return; // 失败静默:按钮还在,下次再试
    setOlderCursor(doc.next_cursor);
    if (doc.rows.length > 0) setRows((prev) => mergeRows(prev, doc.rows));
  }, [olderCursor]);

  const onStreamScroll = (e: UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    nearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    if (el.scrollTop < 48) void loadOlder(); // 上滑触顶自动加载更早
  };

  // T6 说话开仗: 发送→say(意图解析);失败红条带原文重试,不吞错。
  const sendSay = useCallback(async (text: string) => {
    setFlow({ phase: "parsing" });
    const r = await postJSON("/api/chat/say", { text });
    if (!r.ok) {
      const d = r.data as { error?: unknown } | null;
      const msg = typeof d?.error === "string" && d.error ? d.error : "请求失败(HTTP " + r.status + ")";
      setFlow({ phase: "error", message: msg, retry: () => void sendSay(text) });
      return;
    }
    const d = r.data as Record<string, unknown> | null;
    const status = d?.status;
    if (status === "confirm" && d && typeof d.card === "object" && d.card !== null) {
      const c = d.card as Partial<ConfirmCard>;
      if (typeof c.id === "string" && typeof c.target === "string") {
        setFlow({
          phase: "confirm",
          card: {
            kind: typeof c.kind === "string" ? c.kind : "confirm-ignite",
            id: c.id,
            target: c.target,
            scope: Array.isArray(c.scope) ? c.scope.map(String) : [],
            budget: typeof c.budget === "string" ? c.budget : "",
            auth_notice: typeof c.auth_notice === "string" ? c.auth_notice : "",
          },
        });
        return;
      }
    }
    if (status === "ask" && d && Array.isArray(d.questions)) {
      setFlow({ phase: "ask", questions: d.questions.map(String) });
      return;
    }
    if (status === "chat") {
      setFlow({ phase: "chat", reply: String(d?.reply ?? "") });
      return;
    }
    setFlow({ phase: "error", message: "响应形状未知(缺 status/card)", retry: () => void sendSay(text) });
  }, []);

  // 确认双钮: 批/拒都 POST /api/chat/confirm;回执气泡只显服务端结果,
  // 点火时刻不伪造——真点火经 stream 轮询自然到来。
  const sendConfirm = useCallback(async (card: ConfirmCard, approved: boolean) => {
    setFlow({ phase: "busy", card, approved });
    const r = await postJSON("/api/chat/confirm", { id: card.id, approved });
    if (!r.ok) {
      const d = r.data as { error?: unknown } | null;
      const msg = typeof d?.error === "string" && d.error ? d.error : "确认请求失败(HTTP " + r.status + ")";
      setFlow({ phase: "error", message: msg, retry: () => void sendConfirm(card, approved) });
      return;
    }
    const d = r.data as { note?: unknown } | null;
    setFlow({ phase: "result", text: String(d?.note ?? (approved ? "已确认。" : "已取消。")) });
  }, []);

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    void sendSay(text);
  };

  const battles = [...new Set(rows.map((r) => r.battle))].sort();
  const visible = battleFilter ? rows.filter((r) => r.battle === battleFilter) : rows;
  const freshSet = new Set(fresh);
  const exhausted = olderCursor === null;

  return (
    <section data-testid="chat-page" className="flex h-full min-h-0">
      <style>{"@keyframes glds-fade-in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}.row-fade{animation:glds-fade-in .45s ease-out}"}</style>
      <div className="flex min-w-0 flex-1 flex-col">
        {/* 仗过滤 chips(客户端过滤,数据来自已收行) */}
        <div className="flex flex-wrap items-center gap-1.5 border-b border-line px-4 py-2">
          <Chip label="全部" active={battleFilter === null} onClick={() => setBattleFilter(null)} />
          {battles.map((b) => (
            <Chip key={b} label={b} active={battleFilter === b} onClick={() => setBattleFilter(b)} />
          ))}
        </div>
        {/* 断线黄条: 轮询失败显示,恢复自动撤 */}
        {disconnected && (
          <div role="alert" className="border-b border-warn/40 bg-warn/10 px-4 py-1.5 text-fs-a text-warn">
            连接中断,重连中…
          </div>
        )}
        <div
          ref={scrollRef}
          data-testid="chat-stream"
          onScroll={onStreamScroll}
          className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-3"
        >
          <button
            type="button"
            data-testid="load-older"
            disabled={exhausted || loadingOlder}
            onClick={() => void loadOlder()}
            className="mx-auto mb-3 rounded-glds-s border border-line-2 px-3 py-1 text-fs-a text-tx4 hover:text-tx2 disabled:cursor-default disabled:opacity-50"
          >
            {exhausted ? "已到最早" : loadingOlder ? "加载中…" : "加载更早"}
          </button>
          <ul className="flex flex-1 flex-col gap-2">
            {visible.map((r) => (
              <li key={r.key} data-testid="chat-row" data-key={r.key}>
                <MomentCard row={r} fresh={freshSet.has(r.key)} />
              </li>
            ))}
          </ul>
        </div>
        {/* T6 说话开仗交互条: 解析中/问询/闲聊/确认卡/回执/红条(行内,不入流不造假) */}
        {flow.phase !== "idle" && (
          <div data-testid="say-flow" className="border-t border-line px-4 py-2.5">
            {flow.phase === "parsing" && (
              <p data-testid="say-parsing" className="font-mono text-fs-a text-acc">
                指挥→AI 解析中…
              </p>
            )}
            {flow.phase === "ask" && (
              <div data-testid="say-ask" className="rounded-glds-s border border-info/40 px-3 py-2 font-mono text-fs-a leading-6 text-info">
                <p className="text-tx3">还缺关键信息,补一句再发:</p>
                <ul className="mt-0.5 text-tx2">
                  {flow.questions.map((q, i) => (
                    <li key={i}>· {q}</li>
                  ))}
                </ul>
              </div>
            )}
            {flow.phase === "chat" && (
              <p data-testid="say-chat" className="rounded-glds-s border border-line-2 px-3 py-2 font-mono text-fs-a leading-6 text-tx2">
                {flow.reply}
              </p>
            )}
            {flow.phase === "confirm" && (
              <SayConfirmCard
                card={flow.card}
                busy={false}
                onConfirm={() => void sendConfirm(flow.card, true)}
                onCancel={() => void sendConfirm(flow.card, false)}
              />
            )}
            {flow.phase === "busy" && <SayConfirmCard card={flow.card} busy onConfirm={() => {}} onCancel={() => {}} />}
            {flow.phase === "result" && (
              <p data-testid="say-result" className="rounded-glds-s border border-ok/40 px-3 py-2 font-mono text-fs-a leading-6 text-ok">
                {flow.text}
              </p>
            )}
            {flow.phase === "error" && (
              <div
                data-testid="say-error"
                role="alert"
                className="flex flex-wrap items-center gap-2 rounded-glds-s border border-dang/50 px-3 py-2 font-mono text-fs-a leading-6 text-dang"
              >
                <span className="min-w-0 break-all">{flow.message}</span>
                <button
                  type="button"
                  data-testid="say-retry"
                  onClick={flow.retry}
                  className="shrink-0 rounded-glds-s border border-dang/50 px-2 py-0.5 hover:bg-dang/10"
                >
                  重试
                </button>
              </div>
            )}
          </div>
        )}
        {/* 输入常活(T6): 发送即 POST /api/chat/say */}
        <form onSubmit={onSubmit} className="border-t border-line p-3">
          <div className="flex items-center gap-2">
            <input
              data-testid="chat-input"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="对指挥台说一句(目标/范围/预算)…"
              aria-label="指挥台输入"
              className="h-10 min-w-0 flex-1 rounded-glds-s border border-line-2 bg-bg-side px-3 text-fs-b text-tx1 placeholder:text-tx5 focus:border-acc/50 focus:outline-none"
            />
            <button type="submit" className="h-10 rounded-glds-s bg-acc px-4 text-fs-b font-medium text-acc-on">
              发送
            </button>
          </div>
        </form>
      </div>
      {/* 右侧战况板(可收起) */}
      <aside
        data-testid="warboard"
        aria-label="战况板"
        className={
          "flex w-72 shrink-0 flex-col overflow-y-auto border-l border-line bg-bg-side " +
          (boardOpen ? "" : "hidden")
        }
      >
        <div className="flex items-center justify-between border-b border-line px-3 py-2">
          <h2 className="text-fs-a tracking-[2px] text-tx4">战况板</h2>
          <button
            type="button"
            data-testid="warboard-toggle"
            aria-pressed={boardOpen}
            onClick={() => setBoardOpen((v) => !v)}
            className="rounded-glds-s border border-line-2 px-2 py-0.5 text-fs-a text-tx4 hover:text-tx2"
          >
            收起
          </button>
        </div>
        <WbPanel testid="wb-soldiers" title="在跑士兵" items={board?.soldiers ?? []} empty="暂无在跑士兵" />
        <WbPanel testid="wb-findings" title="最新发现" items={board?.findings_latest ?? []} empty="暂无发现" />
        <WbPanel testid="wb-approvals" title="待审批" items={board?.approvals ?? []} empty="暂无待审批" />
      </aside>
    </section>
  );
}
