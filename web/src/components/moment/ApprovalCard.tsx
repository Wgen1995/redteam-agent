import { useState } from "react";

/**
 * 审批卡(T8 内联审批): warboard approvals 待审项 → 流顶出卡。
 *
 * - 一级: 命令原文(event 逐字)+风险句(risk_line,有则显——判不了服务端
 *   给 null,不造假)+关联发现(事件内 FD-x 引用有则显)+超时策略
 *   (timeout_policy)+battle 徽标点;双钮「批准执行/拒绝」。
 * - 提交: POST /api/chat/approve {battle,command_hash,decision}——
 *   提交中双钮禁用;结果→卡转结果态(绿已批准/红已拒绝,带审批号),
 *   审批入链时刻经指挥流轮询自然到来,本卡不伪造;失败红条
 *   (role=alert)带服务器原文+行内重试。
 * - 数据源只读待审: 卡随 warboard 轮询消项自然撤(决后到下轮前由
 *   本地结果态稳显)。
 */

export interface ApprovalItem {
  /** 命令哈希=sha256(revert_cmd),approve 通道同键。 */
  id: string;
  /** 命令原文(账本 timeline event 逐字)。 */
  event: string;
  /** 风险一句(词表判读;判不了=null 不显)。 */
  risk_line?: string | null;
  /** 超时策略文案(如「待审挂起超 30 分钟→保守跳过」)。 */
  timeout_policy?: string | null;
  ts?: string | null;
  battle: string;
  badge: string;
}

type CardPhase =
  | { phase: "idle" }
  | { phase: "busy" }
  | { phase: "done"; decision: "approve" | "reject"; approvalId: string }
  | { phase: "error"; message: string; retry: () => void };

/** 事件文本内的发现引用(FD-x)——有则显,无则不造假。 */
function findingRefOf(event: string): string | null {
  const m = /\b(FD-[A-Za-z0-9-]+)\b/.exec(event);
  return m ? m[1] : null;
}

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

export default function ApprovalCard({ item }: { item: ApprovalItem }) {
  const [state, setState] = useState<CardPhase>({ phase: "idle" });

  const submit = async (decision: "approve" | "reject") => {
    setState({ phase: "busy" });
    const r = await postJSON("/api/chat/approve", {
      battle: item.battle,
      command_hash: item.id,
      decision,
    });
    if (!r.ok) {
      const d = r.data as { error?: unknown } | null;
      const msg = typeof d?.error === "string" && d.error
        ? d.error : "审批请求失败(HTTP " + r.status + ")";
      setState({ phase: "error", message: msg, retry: () => void submit(decision) });
      return;
    }
    const d = r.data as { approval_id?: unknown } | null;
    setState({
      phase: "done",
      decision,
      approvalId: typeof d?.approval_id === "string" ? d.approval_id : "",
    });
  };

  if (state.phase === "done") {
    const approved = state.decision === "approve";
    return (
      <div
        data-testid="approval-done"
        className={
          "rounded-glds-s border px-3 py-2.5 font-mono text-fs-a leading-6 " +
          (approved ? "border-ok/50 bg-ok/10 text-ok" : "border-dang/50 bg-dang/10 text-dang")
        }
      >
        <span className="font-medium">{approved ? "已批准" : "已拒绝"}</span>
        {state.approvalId ? <span className="ml-1 opacity-80">{state.approvalId}</span> : null}
        <span className="text-tx5">——审批已入链,后续时刻经指挥流自然到来</span>
        <p className="mt-1 whitespace-pre-wrap break-all text-tx4">{item.event}</p>
      </div>
    );
  }

  const busy = state.phase === "busy";
  const finding = findingRefOf(item.event);
  return (
    <div
      data-testid="approval-card"
      data-battle={item.battle}
      className="rounded-glds-s border border-warn/50 bg-warn/5 px-3 py-2.5 font-mono text-fs-a leading-6"
    >
      <div className="flex items-center gap-2 text-warn">
        <span
          data-testid="battle-dot"
          title={item.battle}
          aria-label={item.battle}
          className="inline-block size-2 shrink-0 rounded-full"
          style={{ backgroundColor: item.badge }}
        />
        <span className="rounded-glds-s border border-warn/40 px-1.5">待审批</span>
        <span className="text-tx3">{item.battle}</span>
        {item.ts ? <time className="ml-auto shrink-0 text-tx5" dateTime={item.ts}>{item.ts}</time> : null}
      </div>
      <p data-testid="approval-event" className="mt-1.5 whitespace-pre-wrap break-all text-tx2">
        {item.event}
      </p>
      {item.risk_line ? (
        <p data-testid="approval-risk" className="mt-0.5 text-warn">
          风险: {item.risk_line}
        </p>
      ) : null}
      {finding ? (
        <p data-testid="approval-finding" className="mt-0.5 text-dang">
          关联发现: {finding}
        </p>
      ) : null}
      {item.timeout_policy ? (
        <p data-testid="approval-timeout" className="mt-0.5 text-tx5">
          {item.timeout_policy}
        </p>
      ) : null}
      {state.phase === "error" && (
        <div
          data-testid="approval-error"
          role="alert"
          className="mt-2 flex flex-wrap items-center gap-2 rounded-glds-s border border-dang/50 px-2 py-1.5 text-dang"
        >
          <span className="min-w-0 break-all">{state.message}</span>
          <button
            type="button"
            data-testid="approval-retry"
            onClick={state.retry}
            className="shrink-0 rounded-glds-s border border-dang/50 px-2 py-0.5 hover:bg-dang/10"
          >
            重试
          </button>
        </div>
      )}
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          data-testid="approval-approve"
          disabled={busy}
          onClick={() => void submit("approve")}
          className="rounded-glds-s border border-ok/60 bg-ok/15 px-3 py-1 font-medium text-ok hover:bg-ok/25 disabled:opacity-50"
        >
          {busy ? "提交中…" : "批准执行"}
        </button>
        <button
          type="button"
          data-testid="approval-reject"
          disabled={busy}
          onClick={() => void submit("reject")}
          className="rounded-glds-s border border-dang/60 px-3 py-1 text-dang hover:bg-dang/10 disabled:opacity-50"
        >
          {busy ? "提交中…" : "拒绝"}
        </button>
      </div>
    </div>
  );
}
