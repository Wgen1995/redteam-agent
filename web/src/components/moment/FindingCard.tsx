import { useState } from "react";
import MomentCard, { type MomentRow } from "./MomentCard";
import { kindSpec } from "./kinds";

/**
 * 发现时刻卡(T9): add-finding/supersede-finding 行配到
 * /api/chat/findings 的发现 → 升级为发现卡;配不到 → 退回 T7
 * MomentCard 原卡,不硬凑。
 *
 * - 一级: 时间+battle 徽标点+kind 色标(词表着色/权重同源)+发现号+
 *   标题+严重度章+验真态徽(+supersede 行注明更替来源+位置有则显);
 * - 严重度章四色: 引擎 confidence 词表 C1→危(critical 红)/C2→高
 *   (high 琥珀)/C3→中(medium 蓝)/➖🛑→低(low 灰);词表外原样透传
 *   不翻译(data-sev=other 中性);缺=不出章不造级;
 * - 验真态徽三态(不造绿): 已验→绿「机器已验」/REPAIRED→绿「复放
 *   确认」/其余(待验/复验中/REJECTED)→灰「待机器复验」如实;
 * - 二级(点开): 原文逐字(whitespace-pre-wrap)+证据袋引用(有则显,
 *   无则不占位)+位置+kind/key/battle/ts 透明不藏。
 */

/** /api/chat/findings 行(形状校验见 chat.tsx asFindingsDoc)。 */
export interface FindingDoc {
  id: string;
  title: string;
  /** 引擎 confidence 词表原样(C1/C2/C3/➖🛑;缺/坏=null)。 */
  severity: string | null;
  where: string | null;
  verified: boolean;
  replay_state: string;
  /** 证据袋引用(EV 号;无引用=空数组/null)。 */
  evidence: string[] | null;
  battle: string;
  badge: string;
  ts: string | null;
}

/** add-finding/supersede-finding detail → 配对用发现号;解析不中=null。 */
export function findingRefOf(kind: string, detail: string): string | null {
  if (kind === "add-finding") {
    const m = /(?:^|\s)(FD-\S+)/.exec(detail);
    return m ? m[1] : null;
  }
  if (kind === "supersede-finding") {
    // 箭头目标=更替后在册发现(配对新发现;旧发现号进「更替自」注记)
    const m = /^supersede-finding\s+(\S+?)->(\S+)/.exec(detail);
    return m ? m[2] : null;
  }
  return null;
}

/** supersede 行的更替来源(旧发现号);非 supersede/解析不中=null。 */
function supersededFrom(kind: string, detail: string): string | null {
  if (kind !== "supersede-finding") return null;
  const m = /^supersede-finding\s+(\S+?)->(\S+)/.exec(detail);
  return m ? m[1] : null;
}

/** ISO 时间戳 → HH:MM:SS(非 ISO 原样;全 ts 在 title 与二级)。 */
function timeOf(ts: string): string {
  const m = /T(\d{2}:\d{2}:\d{2})/.exec(ts);
  return m ? m[1] : ts;
}

/** 严重度章: 引擎词表 → 四色档;词表外=other 中性原样;缺=不出章。 */
function sevOf(sev: string | null): { tier: string; word: string; cls: string } | null {
  if (sev === null || sev === "") return null;
  const table: Record<string, { tier: string; word: string; cls: string }> = {
    C1: { tier: "critical", word: "危", cls: "border-dang/50 bg-dang/10 text-dang" },
    C2: { tier: "high", word: "高", cls: "border-warn/50 bg-warn/10 text-warn" },
    C3: { tier: "medium", word: "中", cls: "border-info/50 bg-info/10 text-info" },
    "➖🛑": { tier: "low", word: "低", cls: "border-line-2 bg-bg-raise text-tx3" },
  };
  const hit = table[sev];
  if (hit) return hit;
  return { tier: "other", word: sev, cls: "border-line-2 bg-bg-raise text-tx3" };
}

/** 验真态徽三态: 绿仅给通过档(VERIFIED/REPAIRED),其余灰,不造绿。 */
function verifyOf(f: FindingDoc): { state: string; label: string; cls: string } {
  if (f.replay_state === "REPAIRED") {
    return { state: "repaired", label: "复放确认", cls: "border-ok/50 bg-ok/10 text-ok" };
  }
  if (f.verified && (f.replay_state === "已验" || f.replay_state === "VERIFIED")) {
    return { state: "verified", label: "机器已验", cls: "border-ok/50 bg-ok/10 text-ok" };
  }
  return { state: "pending", label: "待机器复验", cls: "border-line-2 bg-bg-raise text-tx3" };
}

export default function FindingCard({
  row,
  finding,
  fresh = false,
}: {
  row: MomentRow;
  finding: FindingDoc | null;
  fresh?: boolean;
}) {
  const [open, setOpen] = useState(false);
  // 配不到=退回 T7 原卡(不硬凑): 词表一级人话+二级原文原样。
  if (!finding) return <MomentCard row={row} fresh={fresh} />;
  const spec = kindSpec(row.kind);
  const sev = sevOf(finding.severity);
  const ver = verifyOf(finding);
  const from = supersededFrom(row.kind, row.detail);
  const evid = finding.evidence ?? [];
  return (
    <div
      data-testid="finding-card"
      data-fd={finding.id}
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
        data-testid="finding-toggle"
        aria-expanded={open}
        title={open ? "收起明细" : "展开明细"}
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left"
      >
        <div className="flex items-start gap-2">
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
          <span data-testid="moment-mark" title={row.kind} aria-label={"kind " + row.kind} className="mt-0.5 shrink-0 opacity-70">
            ◆
          </span>
          <span data-testid="finding-id" title={"发现号 " + finding.id} className="shrink-0 text-tx1">
            {finding.id}
          </span>
          <span data-testid="finding-title" className="min-w-0 break-all text-tx2">
            {finding.title}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-1.5 pl-6">
          {sev && (
            <span
              data-testid="sev-chip"
              data-sev={sev.tier}
              title={"严重度(引擎 confidence) " + String(finding.severity)}
              className={"rounded-glds-s border px-1.5 " + sev.cls}
            >
              {sev.word + "·" + String(finding.severity)}
            </span>
          )}
          <span
            data-testid="verify-chip"
            data-state={ver.state}
            title={"机器复放验真态 " + finding.replay_state}
            className={"rounded-glds-s border px-1.5 " + ver.cls}
          >
            {ver.label}
          </span>
          {from && <span className="text-tx5">更替自 {from}</span>}
          {finding.where && (
            <span data-testid="finding-where" className="text-tx5" title="位置(affected_asset_id)">
              @ {finding.where}
            </span>
          )}
        </div>
      </button>
      {open && (
        <dl
          data-testid="finding-raw"
          className="mt-2 flex flex-col gap-1 border-t border-line/60 pt-2 leading-5 text-tx3"
        >
          <div className="flex gap-2">
            <dt className="shrink-0 text-tx5">原文:</dt>
            <dd className="min-w-0 whitespace-pre-wrap break-all">{row.detail}</dd>
          </div>
          {evid.length > 0 && (
            <div className="flex gap-2">
              <dt className="shrink-0 text-tx5">证据袋:</dt>
              <dd data-testid="finding-evidence" className="min-w-0 break-all">
                {evid.join("、")}
              </dd>
            </div>
          )}
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
