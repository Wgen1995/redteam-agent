import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

/**
 * 任务列表页(P0 T11 件B): 仗卡一览,点进详情(会话签)。
 *
 * - 数据: GET /api/tasks(battles 根枚举单源,含已完跑/复测/草稿不分态);
 *   10s 轮询翻新(状态章/计数/latest 如实演化,失败静默保持旧值);
 *   首载失败红条(role=alert)带行内重试,零假数。
 * - 仗卡: 名(goals.target,缺显仗号)/状态章(执行中绿·其余中性,
 *   title 带态说明)/徽标点(sha256 派生稳定色相同源)/当代 goal(G-x)/
 *   兵数/发现数(ledger_reader 计数如实透传)/最新时刻(HH:MM:SS,
 *   title 带全 ts;无时间线=不造假「—」)。
 * - 空态: 零仗诚实指路(去指挥台开仗),不造卡。
 */

/** GET /api/tasks 行(形状校验见 asTasksDoc,宁缺毋假)。 */
export interface TaskBattle {
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

interface TasksDoc {
  battles: TaskBattle[];
}

const TASKS_POLL_MS = 10000;   // 同战况板/在跑仗条 10s 律

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

function asTasksDoc(v: unknown): TasksDoc | null {
  if (typeof v !== "object" || v === null) return null;
  const battles = (v as { battles?: unknown }).battles;
  if (!Array.isArray(battles)) return null;
  const rows = battles.filter(
    (b): b is TaskBattle =>
      typeof b === "object" &&
      b !== null &&
      typeof (b as TaskBattle).id === "string" &&
      (b as TaskBattle).id !== "" &&
      typeof (b as TaskBattle).name === "string" &&
      typeof (b as TaskBattle).status === "string" &&
      typeof (b as TaskBattle).running === "boolean" &&
      typeof (b as TaskBattle).badge === "string" &&
      typeof (b as TaskBattle).goal === "string" &&
      typeof (b as TaskBattle).soldiers_n === "number" &&
      typeof (b as TaskBattle).findings_n === "number",
  );
  return { battles: rows };
}

/** ISO 时间戳 → HH:MM:SS(非 ISO 原样;全 ts 在 title)。 */
export function timeOf(ts: string): string {
  const m = /T(\d{2}:\d{2}:\d{2})/.exec(ts);
  return m ? m[1] : ts;
}

/** 状态章: 执行中绿(词=服务端 tasks_view 单源),其余中性如实。 */
function StatusChip({ status, detail, running }: { status: string; detail: string; running: boolean }) {
  return (
    <span
      data-testid="task-status"
      data-running={running ? "true" : "false"}
      title={detail || status}
      className={
        "shrink-0 rounded-glds-s border px-1.5 py-0.5 " +
        (running
          ? "border-ok/50 bg-ok/10 text-ok"
          : "border-line-2 bg-bg-raise text-tx3")
      }
    >
      {status}
    </span>
  );
}

export default function TasksPage() {
  const [doc, setDoc] = useState<TasksDoc | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [retryNonce, setRetryNonce] = useState(0);

  const load = useCallback(async () => {
    const d = await fetchJSON("/api/tasks", asTasksDoc);
    if (d === null) {
      setFailed(true);
      setError("任务列表读取失败(服务不可达或响应坏形)");
      return;
    }
    setFailed(false);
    setError(null);
    setDoc(d);
  }, []);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      const d = await fetchJSON("/api/tasks", asTasksDoc);
      if (!alive) return;
      if (d === null) return;            // 轮询败=静默保持旧值
      setFailed(false);
      setError(null);
      setDoc(d);
    };
    void load();
    const id = setInterval(tick, TASKS_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [load, retryNonce]);

  const battles = doc?.battles ?? [];

  return (
    <section data-testid="tasks-page" className="h-full overflow-y-auto">
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
        <h1 className="text-fs-c font-medium text-tx2">
          任务
          <span className="ml-1.5 font-mono text-fs-a text-tx5">{battles.length}</span>
        </h1>
        <Link
          to="/chat"
          className="rounded-glds-s border border-line-2 px-2 py-0.5 text-fs-a text-tx4 hover:text-tx2"
        >
          去指挥台
        </Link>
      </div>
      {error && failed && (
        <div
          data-testid="tasks-error"
          role="alert"
          className="flex flex-wrap items-center gap-2 border-b border-dang/50 px-4 py-2 font-mono text-fs-a text-dang"
        >
          <span className="min-w-0 break-all">{error}</span>
          <button
            type="button"
            data-testid="tasks-retry"
            onClick={() => setRetryNonce((n) => n + 1)}
            className="shrink-0 rounded-glds-s border border-dang/50 px-2 py-0.5 hover:bg-dang/10"
          >
            重试
          </button>
        </div>
      )}
      {battles.length === 0 ? (
        <div
          data-testid="tasks-empty"
          className="flex flex-col items-center gap-3 px-6 py-16 text-center"
        >
          <p className="text-fs-b text-tx4">还没打过仗——去指挥台说一句打哪,开了仗这里就有任务卡。</p>
          <Link
            to="/chat"
            className="rounded-glds-s bg-acc px-3 py-1 text-fs-a font-medium text-acc-on"
          >
            去指挥台
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-2 px-4 py-3">
          {battles.map((b) => (
            <li key={b.id}>
              <Link
                to={"/tasks/" + encodeURIComponent(b.id)}
                data-testid="task-card"
                data-battle={b.id}
                className="block rounded-glds-s border border-line bg-bg-card px-3 py-2.5 font-mono text-fs-a leading-6 transition-colors hover:border-acc/40"
              >
                <div className="flex items-center gap-2">
                  <span
                    data-testid="battle-dot"
                    title={b.id}
                    aria-label={b.id}
                    className="inline-block size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: b.badge }}
                  />
                  <span data-testid="task-name" className="min-w-0 break-all text-tx1">
                    {b.name || b.id}
                  </span>
                  <StatusChip status={b.status} detail={b.status_detail} running={b.running} />
                  <span className="ml-auto shrink-0 text-tx5" title={b.id}>
                    {b.id}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 pl-4 text-tx4">
                  <span data-testid="task-goal" title="当代 goal(代目录)">
                    代 {b.goal || "—"}
                  </span>
                  <span data-testid="task-soldiers" title="在编意图行(战士)计数">
                    兵 {b.soldiers_n}
                  </span>
                  <span data-testid="task-findings" title="发现计数">
                    发现 {b.findings_n}
                  </span>
                  <span
                    data-testid="task-latest"
                    title={b.latest_ts ?? ""}
                    className="ml-auto text-tx5"
                  >
                    {b.latest_ts ? "最新 " + timeOf(b.latest_ts) : "—"}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
