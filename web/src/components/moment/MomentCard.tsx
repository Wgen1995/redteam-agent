import { useState } from "react";
import { kindSpec } from "./kinds";

/**
 * 时刻卡(T7 两级播报): 引擎账本行 → 指挥级两级呈现。
 *
 * - 一级(常显): 一句人话 = 时间(HH:MM:SS,title 带全 ts)+kind 色标
 *   (title=kind,色=词表着色)+人话(kinds.ts 词表;未知 kind 兜底
 *   「[kind] detail 原样」零编造)+battle 徽标点(服务端派生稳定色)。
 * - 二级(点开): 原样 detail/kind/key/battle/ts——透明不藏,引擎原账本
 *   永远可查(多行原文 whitespace-pre-wrap 逐字保留)。
 * - 权重: loud 加重(font-medium)/dim 轻描(opacity-55,心跳类);
 *   fresh=新行淡入(chat 流动画标记透传)。
 */

export interface MomentRow {
  key: string;
  ts: string;
  kind: string;
  detail: string;
  battle: string;
  badge: string;
}

/** ISO 时间戳 → HH:MM:SS(非 ISO 原样;全 ts 在 title 与二级)。 */
function timeOf(ts: string): string {
  const m = /T(\d{2}:\d{2}:\d{2})/.exec(ts);
  return m ? m[1] : ts;
}

export default function MomentCard({ row, fresh = false }: { row: MomentRow; fresh?: boolean }) {
  const [open, setOpen] = useState(false);
  const spec = kindSpec(row.kind);
  return (
    <div
      data-testid={"row-" + row.key}
      data-kind={row.kind}
      data-weight={spec.weight}
      className={
        "rounded-glds-s border bg-bg-card px-3 py-2 font-mono text-fs-a leading-6 " +
        spec.tone(row.detail) +
        (spec.weight === "loud" ? " font-medium" : "") +
        (spec.weight === "dim" ? " opacity-55" : "") +
        (fresh ? " row-fade" : "")
      }
    >
      <button
        type="button"
        data-testid="moment-toggle"
        aria-expanded={open}
        title={open ? "收起原文" : "展开原文"}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start gap-2 text-left"
      >
        <span
          data-testid="battle-dot"
          title={row.battle}
          aria-label={row.battle}
          className="mt-2 inline-block size-2 shrink-0 rounded-full"
          style={{ backgroundColor: row.badge }}
        />
        <time data-testid="moment-time" dateTime={row.ts} title={row.ts} className="shrink-0 text-tx5">
          {timeOf(row.ts)}
        </time>
        <span data-testid="moment-mark" title={row.kind} aria-label={"kind " + row.kind} className="shrink-0 opacity-70">
          ◆
        </span>
        <span data-testid="moment-line" className="min-w-0 break-all text-tx2">
          {spec.line(row.detail)}
        </span>
      </button>
      {open && (
        <dl
          data-testid="moment-raw"
          className="mt-2 flex flex-col gap-1 border-t border-line/60 pt-2 leading-5 text-tx3"
        >
          <div className="flex gap-2">
            <dt className="shrink-0 text-tx5">原文:</dt>
            <dd className="min-w-0 whitespace-pre-wrap break-all">{row.detail}</dd>
          </div>
          <div>
            <span className="text-tx5">kind: </span>
            {row.kind}
          </div>
          <div>
            <span className="text-tx5">key: </span>
            <span className="break-all">{row.key}</span>
          </div>
          <div>
            <span className="text-tx5">battle: </span>
            {row.battle}
          </div>
          <div>
            <span className="text-tx5">ts: </span>
            {row.ts}
          </div>
        </dl>
      )}
    </div>
  );
}
