import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BrandMark } from "../components/brand";
import { DEMO_FLAG } from "../lib/api";
import { NAV_GROUPS, type NavItem } from "./ia";

/**
 * 应用壳(P0 T4): 20 页 IA 侧栏(作战7/机组4/系统9)+顶栏三件(搜索/预算表/全停)。
 *
 * - badge 数据=GET /api/overview(T4 件A): 指挥台旁标进行中仗数,
 *   审批红点=待审数;请求失败或形状不对→静默藏 badge,不造假数。
 * - demo 黄条自 T3 的 /chat 页挪入顶栏(sessionStorage glds.demo)。
 * - 顶栏三件均占位: 全停红钮禁用态+title「P1 接线」。
 * - 仅桌面(移动端 P 后续任务);当前页高亮=aria-current="page"。
 */

export interface Overview {
  active_battles: number;
  soldiers_running: number;
  pending_approvals: number;
}

/** GET /api/overview;失败/坏形状→null(调用方藏 badge;壳内自用)。 */
async function fetchOverview(): Promise<Overview | null> {
  try {
    const res = await fetch("/api/overview", { credentials: "same-origin" });
    if (!res.ok) return null;
    const b: Partial<Overview> = await res.json();
    const okNum = (v: unknown): v is number =>
      typeof v === "number" && Number.isFinite(v);
    if (
      !okNum(b.active_battles) ||
      !okNum(b.soldiers_running) ||
      !okNum(b.pending_approvals)
    ) {
      return null;
    }
    return {
      active_battles: b.active_battles,
      soldiers_running: b.soldiers_running,
      pending_approvals: b.pending_approvals,
    };
  } catch {
    return null; // 断网/非 JSON 一律静默——宁缺毋假
  }
}

function useOverview(): Overview | null {
  const [ov, setOv] = useState<Overview | null>(null);
  useEffect(() => {
    let alive = true;
    fetchOverview().then((d) => {
      if (alive) setOv(d);
    });
    return () => {
      alive = false;
    };
  }, []);
  return ov;
}

function Badge({
  kind,
  count,
  title,
}: {
  kind: "battles" | "approvals";
  count: number;
  title: string;
}) {
  if (count <= 0) return null; // 零不是事件;失败态在数据层已拦
  return (
    <span
      data-testid={`badge-${kind}`}
      title={title}
      className={
        "ml-auto inline-flex min-w-5 items-center justify-center rounded-full px-1.5 " +
        "font-mono text-fs-a leading-4 " +
        (kind === "approvals"
          ? "bg-dang/15 text-dang"
          : "bg-acc-dim text-acc")
      }
    >
      {count}
    </span>
  );
}

function SideItem({
  item,
  battles,
  approvals,
}: {
  item: NavItem;
  battles?: number;
  approvals?: number;
}) {
  return (
    <NavLink
      to={item.path}
      className={({ isActive }) =>
        "flex items-center gap-2 rounded-glds-s px-2.5 py-1.5 text-fs-b transition-colors " +
        (isActive
          ? "bg-bg-hover font-medium text-tx1"
          : "text-tx3 hover:bg-bg-hover hover:text-tx2")
      }
    >
      <span>{item.name}</span>
      {item.path === "/chat" && (
        <Badge kind="battles" count={battles ?? 0} title="进行中仗数" />
      )}
      {item.path === "/approvals" && (
        <Badge kind="approvals" count={approvals ?? 0} title="待审批数" />
      )}
    </NavLink>
  );
}

function TopBar() {
  const demo = sessionStorage.getItem(DEMO_FLAG) === "1";
  return (
    <header
      data-testid="topbar"
      className="sticky top-0 z-10 border-b border-line bg-bg-side/95"
    >
      {demo && (
        <div
          role="status"
          className="border-b border-warn/40 bg-warn/10 px-4 py-1 text-fs-a text-warn"
        >
          演示模式:未设密钥
        </div>
      )}
      <div className="flex items-center gap-3 px-4 py-2.5">
        <input
          type="search"
          aria-label="全局搜索"
          placeholder="全局搜索(占位)"
          disabled
          className="h-8 w-56 rounded-glds-s border border-line-2 bg-bg-raise px-2.5 text-fs-b text-tx5 placeholder:text-tx5"
        />
        <button
          type="button"
          disabled
          className="h-8 cursor-not-allowed rounded-glds-s border border-line-2 bg-bg-raise px-3 text-fs-b text-tx5"
        >
          预算表
        </button>
        <button
          type="button"
          disabled
          title="P1 接线"
          className="ml-auto h-8 cursor-not-allowed rounded-glds-s border border-dang/50 bg-dang/10 px-3 text-fs-b text-dang"
        >
          全停
        </button>
      </div>
    </header>
  );
}

export function AppShell() {
  const overview = useOverview();
  return (
    <div className="flex h-dvh overflow-hidden bg-bg">
      <aside className="flex w-56 shrink-0 flex-col border-r border-line bg-bg-side">
        <div className="flex items-center gap-2 border-b border-line px-4 py-3 text-acc">
          <BrandMark size={18} />
          <span className="text-fs-b font-semibold tracking-[0.3px] text-tx1">
            GraphLed
          </span>
        </div>
        <nav
          aria-label="全局导航"
          className="flex-1 overflow-y-auto px-2 py-3"
        >
          {NAV_GROUPS.map((g) => (
            <div key={g.label} role="group" aria-label={g.label} className="mb-4">
              <div className="px-2.5 pb-1 text-fs-a tracking-[2px] text-tx5">
                {g.label}
              </div>
              <div className="flex flex-col gap-0.5">
                {g.items.map((item) => (
                  <SideItem
                    key={item.path}
                    item={item}
                    battles={overview?.active_battles}
                    approvals={overview?.pending_approvals}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppShell;
