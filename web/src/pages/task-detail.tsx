import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import FindingCard, { findingRefOf, type FindingDoc } from "../components/moment/FindingCard";
import { timeOf } from "./tasks";

/**
 * 任务详情·会话签(P0 T11 件B): 仗头+会话卡组+组内时刻流。
 *
 * - 仗头: 状态章/徽标/当代 goal/goals 简述+兵数/发现数/最新时刻
 *   (GET /api/tasks/:id;10s 轮询翻新,失败静默保持旧值;404=未知仗
 *   空态如实,不造详情)。
 * - 会话签区: 该仗 timeline 按战士/意图分组(服务端单源归组),每战士/
 *   意图一会话卡(标签/行数/起止);点开=组内时刻流。
 * - 组内时刻流: GET /api/tasks/:id/sessions/:key——行形状同指挥流
 *   (T5),复用 FindingCard/MomentCard 渲染(发现行配对升发现卡,
 *   /api/chat/findings?battle= 30s 轮询同指挥台律;配不到回退原卡);
 *   10s 尾轮询按 key 去重追加;「加载更早」按 before_key 翻页。
 * - 返回列表钮常在(含未知仗空态);深链 /tasks/:id 直达。
 */

/** GET /api/tasks/:id 会话组行。 */
interface Session {
  session_key: string;
  label: string;
  rows_n: number;
  first_ts: string;
  last_ts: string;
}

/** GET /api/tasks/:id 详情(列表字段+简述+会话分组)。 */
interface DetailDoc {
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

/** 组流行(同指挥流 StreamRow 形状)。 */
interface StreamRow {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

const DETAIL_POLL_MS = 10000;   // 仗头/会话卡 10s 翻新(战况板同律)
const STREAM_POLL_MS = 10000;   // 组内时刻流 10s 尾轮询
const FINDINGS_POLL_MS = 30000; // 发现配对面 30s(指挥台 T9 同律)

/** 拉取(带状态码);网络失败 status=0。404 与网络错分流靠它。 */
async function fetchStatusJSON(url: string): Promise<{ ok: boolean; status: number; data: unknown }> {
  try {
    const res = await fetch(url, { credentials: "same-origin" });
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return {
      ok: false, status: 0,
      data: { error: "网络失败: " + (e instanceof Error ? e.message : String(e)) },
    };
  }
}

async function fetchJSON<T>(url: string, check: (v: unknown) => T | null): Promise<T | null> {
  const r = await fetchStatusJSON(url);
  return r.ok ? check(r.data) : null;
}

function asDetailDoc(v: unknown): DetailDoc | null {
  if (typeof v !== "object" || v === null) return null;
  const d = v as Record<string, unknown>;
  const sessions = d.sessions;
  if (
    typeof d.id !== "string" ||
    typeof d.name !== "string" ||
    typeof d.status !== "string" ||
    typeof d.running !== "boolean" ||
    typeof d.badge !== "string" ||
    typeof d.goal !== "string" ||
    typeof d.soldiers_n !== "number" ||
    typeof d.findings_n !== "number" ||
    !Array.isArray(sessions)
  ) {
    return null;
  }
  const rows = sessions.filter(
    (s): s is Session =>
      typeof s === "object" &&
      s !== null &&
      typeof (s as Session).session_key === "string" &&
      (s as Session).session_key !== "" &&
      typeof (s as Session).label === "string" &&
      typeof (s as Session).rows_n === "number" &&
      typeof (s as Session).first_ts === "string" &&
      typeof (s as Session).last_ts === "string",
  );
  return {
    id: d.id,
    name: d.name,
    status: d.status,
    status_detail: typeof d.status_detail === "string" ? d.status_detail : "",
    running: d.running,
    badge: d.badge,
    goal: d.goal,
    soldiers_n: d.soldiers_n,
    findings_n: d.findings_n,
    latest_ts: typeof d.latest_ts === "string" ? d.latest_ts : null,
    objective: typeof d.objective === "string" ? d.objective : "",
    sessions: rows,
  };
}

function asStreamDoc(v: unknown): { rows: StreamRow[]; next_cursor: string | null } | null {
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

function asFindingsDoc(v: unknown): FindingDoc[] | null {
  if (!Array.isArray(v)) return null;
  return v.filter(
    (r): r is FindingDoc =>
      typeof r === "object" &&
      r !== null &&
      typeof (r as FindingDoc).id === "string" &&
      (r as FindingDoc).id !== "" &&
      typeof (r as FindingDoc).title === "string" &&
      typeof (r as FindingDoc).verified === "boolean" &&
      typeof (r as FindingDoc).replay_state === "string" &&
      typeof (r as FindingDoc).battle === "string" &&
      typeof (r as FindingDoc).badge === "string",
  );
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

function BackButton({ to, testid, label }: { to: string; testid: string; label: string }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="shrink-0 rounded-glds-s border border-line-2 px-2 py-0.5 text-fs-a text-tx4 hover:text-tx2"
    >
      ← {label}
    </Link>
  );
}

export default function TaskDetailPage() {
  const { id = "" } = useParams();
  const battle = decodeURIComponent(id);
  const [detail, setDetail] = useState<DetailDoc | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryNonce, setRetryNonce] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [rows, setRows] = useState<StreamRow[]>([]);
  const [olderCursor, setOlderCursor] = useState<string | null | undefined>(undefined);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [findings, setFindings] = useState<FindingDoc[] | null>(null);
  const loadingOlderRef = useRef(false);

  // 仗头+会话分组: 首载+10s 轮询(败=静默保持旧值;404=未知仗空态停轮询)。
  useEffect(() => {
    let alive = true;
    let stop = false;
    const tick = async () => {
      const r = await fetchStatusJSON("/api/tasks/" + encodeURIComponent(battle));
      if (!alive) return;
      if (r.status === 404) {
        setNotFound(true);
        setDetail(null);
        stop = true;
        return;
      }
      if (!r.ok) {
        setError("任务详情读取失败(HTTP " + r.status + ")");
        return;
      }
      const d = asDetailDoc(r.data);
      if (d === null) {
        setError("响应形状未知(缺 id/status/sessions)");
        return;
      }
      setError(null);
      setNotFound(false);
      setDetail(d);
    };
    void tick();
    const timer = setInterval(() => {
      if (!stop) void tick();
    }, DETAIL_POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [battle, retryNonce]);

  // 会话选开: 重置流面。换仗/换组时旧行不残留。
  useEffect(() => {
    setRows([]);
    setOlderCursor(undefined);
  }, [battle, selected]);

  // 组内时刻流: 首窗+10s 尾轮询按 key 去重追加;失败静默(不造假)。
  useEffect(() => {
    if (selected === null) return;
    let alive = true;
    const url =
      "/api/tasks/" + encodeURIComponent(battle) +
      "/sessions/" + encodeURIComponent(selected);
    const tick = async () => {
      const doc = await fetchJSON(url, asStreamDoc);
      if (!alive || doc === null) return;
      setRows((prev) => {
        const merged = mergeRows(prev, doc.rows);
        return merged === prev ? prev : merged;
      });
      setOlderCursor((prev) => (prev === undefined ? doc.next_cursor : prev));
    };
    void tick();
    const timer = setInterval(tick, STREAM_POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [battle, selected]);

  // 发现配对面(组流发现行升发现卡): 30s 轮询同指挥台 T9 律;败=回退原卡。
  useEffect(() => {
    if (selected === null) return;
    let alive = true;
    const tick = async () => {
      const doc = await fetchJSON(
        "/api/chat/findings?battle=" + encodeURIComponent(battle),
        asFindingsDoc,
      );
      if (alive && doc !== null) setFindings(doc);
    };
    void tick();
    const timer = setInterval(tick, FINDINGS_POLL_MS);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [battle, selected]);

  const loadOlder = useCallback(async () => {
    if (loadingOlderRef.current || !olderCursor || selected === null) return;
    loadingOlderRef.current = true;
    setLoadingOlder(true);
    const doc = await fetchJSON(
      "/api/tasks/" + encodeURIComponent(battle) +
        "/sessions/" + encodeURIComponent(selected) +
        "?before_key=" + encodeURIComponent(olderCursor),
      asStreamDoc,
    );
    loadingOlderRef.current = false;
    setLoadingOlder(false);
    if (doc === null) return; // 失败静默:按钮还在,下次再试
    setOlderCursor(doc.next_cursor);
    if (doc.rows.length > 0) setRows((prev) => mergeRows(prev, doc.rows));
  }, [battle, selected, olderCursor]);

  // 发现配对索引: (battle,id) 仗优先,同号异仗兜底全局取首个(指挥台同律)。
  const lookupFinding = useMemo(() => {
    const byBattle = new Map<string, FindingDoc>();
    const byId = new Map<string, FindingDoc>();
    for (const f of findings ?? []) {
      byBattle.set(f.battle + "\u0000" + f.id, f);
      if (!byId.has(f.id)) byId.set(f.id, f);
    }
    return (b: string, fd: string): FindingDoc | null =>
      byBattle.get(b + "\u0000" + fd) ?? byId.get(fd) ?? null;
  }, [findings]);

  if (notFound) {
    return (
      <section
        data-testid="task-not-found"
        className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center"
      >
        <h1 className="text-fs-d font-medium text-tx2">查无此仗</h1>
        <p className="max-w-md text-fs-b leading-[1.8] text-tx4">
          账本里没有这仗(或已换代)——回任务列表看在册的仗。
        </p>
        <BackButton to="/tasks" testid="back-to-tasks" label="返回任务列表" />
      </section>
    );
  }

  if (detail === null) {
    return (
      <section data-testid="task-detail-loading" className="flex h-full items-center justify-center p-6">
        {error ? (
          <div
            data-testid="detail-error"
            role="alert"
            className="flex flex-wrap items-center gap-2 rounded-glds-s border border-dang/50 px-3 py-2 font-mono text-fs-a text-dang"
          >
            <span className="min-w-0 break-all">{error}</span>
            <button
              type="button"
              data-testid="detail-retry"
              onClick={() => setRetryNonce((n) => n + 1)}
              className="shrink-0 rounded-glds-s border border-dang/50 px-2 py-0.5 hover:bg-dang/10"
            >
              重试
            </button>
          </div>
        ) : (
          <p className="font-mono text-fs-a text-tx4">读取任务详情中…</p>
        )}
      </section>
    );
  }

  const exhausted = olderCursor === null;
  const selSession = detail.sessions.find((s) => s.session_key === selected) ?? null;

  return (
    <section data-testid="task-detail" className="flex h-full min-h-0 flex-col">
      {/* 仗头 */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-2.5">
        <BackButton to="/tasks" testid="back-to-tasks" label="任务列表" />
        <span
          data-testid="battle-dot"
          title={detail.id}
          aria-label={detail.id}
          className="inline-block size-2 shrink-0 rounded-full"
          style={{ backgroundColor: detail.badge }}
        />
        <h1 data-testid="task-detail-name" className="min-w-0 break-all text-fs-c font-medium text-tx1">
          {detail.name || detail.id}
        </h1>
        <span
          data-testid="task-status"
          data-running={detail.running ? "true" : "false"}
          title={detail.status_detail || detail.status}
          className={
            "shrink-0 rounded-glds-s border px-1.5 py-0.5 " +
            (detail.running
              ? "border-ok/50 bg-ok/10 text-ok"
              : "border-line-2 bg-bg-raise text-tx3")
          }
        >
          {detail.status}
        </span>
        <span data-testid="task-goal" title="当代 goal(代目录)" className="shrink-0 font-mono text-fs-a text-tx4">
          代 {detail.goal || "—"}
        </span>
        <span className="ml-auto flex shrink-0 items-center gap-3 font-mono text-fs-a text-tx4">
          <span data-testid="task-soldiers" title="在编意图行(战士)计数">
            兵 {detail.soldiers_n}
          </span>
          <span data-testid="task-findings" title="发现计数">
            发现 {detail.findings_n}
          </span>
          <span
            data-testid="task-latest"
            title={detail.latest_ts ?? ""}
            className="text-tx5"
          >
            {detail.latest_ts ? "最新 " + timeOf(detail.latest_ts) : "—"}
          </span>
        </span>
      </div>
      {detail.objective && (
        <p data-testid="task-objective" className="border-b border-line px-4 py-1.5 text-fs-a leading-6 text-tx4">
          {detail.objective}
        </p>
      )}
      {error && (
        <p role="alert" className="border-b border-warn/40 bg-warn/10 px-4 py-1 font-mono text-fs-a text-warn">
          {error}(轮询会自动重试)
        </p>
      )}
      {/* 会话签区: 未选组=会话卡组;选开=组内时刻流 */}
      {selected === null ? (
        <div data-testid="session-tabs" className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
          <h2 className="mb-2 text-fs-a tracking-[2px] text-tx4">
            会话签
            <span className="ml-1.5 font-mono text-tx5">{detail.sessions.length}</span>
            <span className="ml-2 text-tx5">每战士/意图一会话——点开看组内时刻流</span>
          </h2>
          {detail.sessions.length === 0 ? (
            <p data-testid="session-empty" className="text-fs-a text-tx5">
              该仗时间线上还没有战士/意图会话(草稿或无代 goal)。
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {detail.sessions.map((s) => (
                <li key={s.session_key}>
                  <button
                    type="button"
                    data-testid="session-card"
                    data-key={s.session_key}
                    title={"会话 " + s.session_key}
                    onClick={() => setSelected(s.session_key)}
                    className="w-full rounded-glds-s border border-line bg-bg-card px-3 py-2 text-left font-mono text-fs-a leading-6 transition-colors hover:border-acc/40"
                  >
                    <div className="flex items-center gap-2">
                      <span data-testid="session-label" className="min-w-0 break-all text-tx1">
                        {s.label}
                      </span>
                      <span className="ml-auto shrink-0 text-tx4">{s.rows_n} 行</span>
                    </div>
                    <div className="mt-0.5 text-tx5">
                      {timeOf(s.first_ts)} → {timeOf(s.last_ts)}
                      <span className="ml-2" title="会话键(归组线索)">
                        {s.session_key}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <div data-testid="session-stream" className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-3">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              data-testid="back-to-sessions"
              onClick={() => setSelected(null)}
              className="shrink-0 rounded-glds-s border border-line-2 px-2 py-0.5 text-fs-a text-tx4 hover:text-tx2"
            >
              ← 会话签
            </button>
            <span className="min-w-0 break-all font-mono text-fs-a text-tx2">
              {selSession ? selSession.label : selected}
              {selSession ? (
                <span className="ml-1.5 text-tx5">{selSession.rows_n} 行</span>
              ) : null}
            </span>
          </div>
          <button
            type="button"
            data-testid="load-older"
            disabled={exhausted || loadingOlder}
            onClick={() => void loadOlder()}
            className="mx-auto mb-3 rounded-glds-s border border-line-2 px-3 py-1 text-fs-a text-tx4 hover:text-tx2 disabled:cursor-default disabled:opacity-50"
          >
            {exhausted ? "已到最早" : loadingOlder ? "加载中…" : "加载更早"}
          </button>
          <ul className="flex flex-1 flex-col gap-2 pb-2">
            {rows.map((r) => {
              const ref = findingRefOf(r.kind, r.detail);
              return (
                <li key={r.key} data-testid="session-row" data-key={r.key}>
                  <FindingCard row={r} finding={ref ? lookupFinding(r.battle, ref) : null} />
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}
