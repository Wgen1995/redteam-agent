import { useCallback, useEffect, useState } from "react";

/**
 * T12 发现页: 统计条+过滤章(严重度/验真态/仗)+发现列表+灰卡区(仅待验,
 * 空不占位)+详情抽屉(证据袋明细+复放史)+重验(桥→tanyin-replay 真重放,
 * 判定如实回报;状态回写走验证官 settle 门,本页不代写)。
 * 30s 轮询翻新(验真态随复放终态演化,绿不滞留);失败红条不造假。
 */

interface Finding {
  id: string; title: string; severity: string; where: string;
  verified: boolean; replay_state: string; evidence: string[];
  battle: string; badge: string; ts: string | null;
}
interface EvDetail { id: string; kind?: string; created?: string; card_path?: string; missing?: boolean }
interface ReplayHist { ev: string; seq: number; verdict: string }
interface Detail extends Finding { evidence_detail: EvDetail[]; replay_history: ReplayHist[] }

const SEV_STYLE: Record<string, string> = {
  C1: "border-dang/50 bg-dang/10 text-dang",
  C2: "border-warn/50 bg-warn/10 text-warn",
  C3: "border-info/50 bg-info/10 text-info",
};
const SEV_LABEL: Record<string, string> = { C1: "危·C1", C2: "高·C2", C3: "中·C3" };

function SevChip({ sev }: { sev: string }) {
  const cls = SEV_STYLE[sev];
  if (!cls) {
    return <span className="rounded border border-line-2 px-1.5 py-0.5 fs-e text-tx3">{sev || "无级"}</span>;
  }
  return <span className={"rounded border px-1.5 py-0.5 fs-e " + cls}>{SEV_LABEL[sev]}</span>;
}

function VerdictBadge({ f }: { f: Finding }) {
  if (f.verified) {
    return <span className="rounded border border-ok/50 bg-ok/10 px-1.5 py-0.5 fs-e text-ok">机器已验</span>;
  }
  return <span className="rounded border border-line-2 px-1.5 py-0.5 fs-e text-tx3">待机器复验</span>;
}

export default function FindingsPage() {
  const [rows, setRows] = useState<Finding[]>([]);
  const [err, setErr] = useState<string>("");
  const [sev, setSev] = useState<string>("");
  const [state, setState] = useState<string>("");
  const [battle, setBattle] = useState<string>("");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [busy, setBusy] = useState<string>("");
  const [note, setNote] = useState<string>("");
  const [rvErr, setRvErr] = useState<string>("");

  const load = useCallback(async () => {
    const q = new URLSearchParams();
    if (sev) q.set("severity", sev);
    if (state) q.set("state", state);
    if (battle) q.set("battle", battle);
    try {
      const r = await fetch("/api/findings?" + q.toString());
      if (!r.ok) throw new Error("HTTP " + r.status);
      setRows(await r.json());
      setErr("");
    } catch (e) {
      setErr("发现清单拉取失败: " + String(e));
    }
  }, [sev, state, battle]);

  useEffect(() => {
    void load();
    const t = setInterval(() => void load(), 30000);
    return () => clearInterval(t);
  }, [load]);

  async function openDetail(id: string) {
    setDetail(null);
    setRvErr("");
    try {
      const r = await fetch("/api/findings/" + id);
      if (!r.ok) throw new Error("HTTP " + r.status);
      setDetail(await r.json());
    } catch (e) {
      setRvErr("详情拉取失败: " + String(e));
    }
  }

  async function reverify(id: string) {
    setBusy(id);
    setRvErr("");
    setNote("");
    try {
      const r = await fetch("/api/findings/" + id + "/reverify", { method: "POST" });
      const doc = await r.json().catch(() => ({}) as Record<string, unknown>);
      if (!r.ok) throw new Error(String(doc.error || "HTTP " + r.status));
      const results = (doc.results || []) as Array<{ ev: string; verdict: string | null; note?: string }>;
      const parts = results.map((x) => x.ev + "→" + (x.verdict || x.note || "无判定"));
      setNote((parts.length ? parts.join(";") + ";" : "") + String(doc.state_note || ""));
      void load();
    } catch (e) {
      setRvErr(String(e));
    } finally {
      setBusy("");
    }
  }

  const pending = rows.filter((f) => !f.verified);
  const battles = Array.from(new Set(rows.map((f) => f.battle)));
  const danger = rows.filter((f) => f.severity === "C1" || f.severity === "C2").length;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
      <h1 className="fs-c text-tx1">发现</h1>
      {err && <div role="alert" className="rounded border border-dang/50 bg-dang/10 px-3 py-2 fs-e text-dang">{err}</div>}

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-line-1 bg-bg2 px-4 py-3">
        <span className="fs-e text-tx3">总数 <b data-testid="stat-total" className="text-tx1">{rows.length}</b></span>
        <span className="fs-e text-tx3">危高 <b data-testid="stat-danger" className="text-dang">{danger}</b></span>
        <span className="fs-e text-tx3">已验 <b data-testid="stat-verified" className="text-ok">{rows.length - pending.length}</b></span>
        <span className="fs-e text-tx3">待验 <b data-testid="stat-pending" className="text-tx3">{pending.length}</b></span>
      </div>

      <div className="flex flex-wrap gap-2">
        {["C1", "C2", "C3"].map((s) => (
          <button key={s} data-testid={"chip-sev-" + s} onClick={() => setSev(sev === s ? "" : s)}
            className={"rounded-full border px-3 py-1 fs-e " + (sev === s ? "border-acc text-acc" : "border-line-2 text-tx3")}>
            {SEV_LABEL[s]}
          </button>
        ))}
        <span className="mx-1 w-px bg-line-2" />
        <button data-testid="chip-state-all" onClick={() => setState("")}
          className={"rounded-full border px-3 py-1 fs-e " + (state === "" ? "border-acc text-acc" : "border-line-2 text-tx3")}>全部态</button>
        <button data-testid="chip-state-verified" onClick={() => setState("verified")}
          className={"rounded-full border px-3 py-1 fs-e " + (state === "verified" ? "border-acc text-acc" : "border-line-2 text-tx3")}>已验</button>
        <button data-testid="chip-state-pending" onClick={() => setState("pending")}
          className={"rounded-full border px-3 py-1 fs-e " + (state === "pending" ? "border-acc text-acc" : "border-line-2 text-tx3")}>待验</button>
        {battles.length > 1 && (
          <span className="mx-1 w-px bg-line-2" />
        )}
        {battles.length > 1 && battles.map((b) => (
          <button key={b} onClick={() => setBattle(battle === b ? "" : b)}
            className={"rounded-full border px-3 py-1 fs-e " + (battle === b ? "border-acc text-acc" : "border-line-2 text-tx3")}>{b}</button>
        ))}
      </div>

      {pending.length > 0 && state !== "verified" && (
        <div data-testid="grey-zone" className="flex flex-col gap-2 rounded-lg border border-line-2 bg-bg2/50 p-3">
          <div className="fs-e text-tx3">灰卡区 · 待机器复验({pending.length})</div>
          {pending.map((f) => (
            <div key={f.id} className="flex items-center gap-3 rounded border border-line-2 bg-bg1 px-3 py-2">
              <span className="size-2 shrink-0 rounded-full" style={{ background: f.badge }} />
              <span className="font-mono fs-e text-tx2">{f.id}</span>
              <span className="truncate fs-e text-tx1">{f.title}</span>
              <SevChip sev={f.severity} />
              <button data-testid={"reverify-" + f.id} disabled={busy === f.id}
                onClick={() => void reverify(f.id)}
                className="ml-auto rounded border border-line-2 px-2 py-1 fs-e text-tx2 disabled:opacity-50">
                {busy === f.id ? "复验中…" : "重新复验"}
              </button>
              <button onClick={() => void openDetail(f.id)} className="rounded border border-line-2 px-2 py-1 fs-e text-tx3">详情</button>
            </div>
          ))}
        </div>
      )}
      {note && <div data-testid="reverify-note" className="rounded border border-info/50 bg-info/10 px-3 py-2 fs-e text-info">{note}</div>}
      {rvErr && <div role="alert" className="rounded border border-dang/50 bg-dang/10 px-3 py-2 fs-e text-dang">{rvErr}</div>}

      <div className="flex flex-col gap-2">
        {rows.map((f) => (
          <button key={f.id} data-testid={"row-" + f.id} onClick={() => void openDetail(f.id)}
            className="flex items-center gap-3 rounded-lg border border-line-1 bg-bg2 px-3 py-2 text-left hover:border-acc/60">
            <span className="size-2 shrink-0 rounded-full" style={{ background: f.badge }} />
            <span className="font-mono fs-e text-tx2">{f.id}</span>
            <span className="flex-1 truncate fs-e text-tx1">{f.title}</span>
            <SevChip sev={f.severity} />
            <VerdictBadge f={f} />
            <span className="fs-e text-tx3">{(f.ts || "").slice(11, 19)}</span>
          </button>
        ))}
      </div>

      {detail && (
        <div data-testid={"drawer-" + detail.id} className="fixed inset-y-0 right-0 z-20 flex w-full max-w-md flex-col gap-3 overflow-y-auto border-l border-line-1 bg-bg1 p-5">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full" style={{ background: detail.badge }} />
            <span className="font-mono fs-e text-tx2">{detail.id}</span>
            <SevChip sev={detail.severity} />
            <VerdictBadge f={detail} />
            <button onClick={() => setDetail(null)} className="ml-auto rounded border border-line-2 px-2 py-1 fs-e text-tx3">关闭</button>
          </div>
          <div className="fs-c text-tx1">{detail.title}</div>
          {detail.where && <div className="fs-e text-tx3">位置 {detail.where}</div>}
          <div className="fs-e text-tx3">证据袋({detail.evidence_detail.length})</div>
          {detail.evidence_detail.map((e) => (
            <div key={e.id} className="rounded border border-line-2 px-2 py-1 font-mono fs-e text-tx2">
              {e.id}{e.missing ? " · 引用悬空" : " · " + (e.kind || "") + " · " + (e.created || "")}
            </div>
          ))}
          <div className="fs-e text-tx3">复放史({detail.replay_history.length})</div>
          {detail.replay_history.map((h, i) => (
            <div key={i} className="font-mono fs-e text-tx2">{h.ev} #{h.seq} → {h.verdict}</div>
          ))}
          {!detail.verified && (
            <button data-testid={"reverify-" + detail.id} disabled={busy === detail.id}
              onClick={() => void reverify(detail.id)}
              className="rounded border border-acc/60 px-3 py-2 fs-e text-acc disabled:opacity-50">
              {busy === detail.id ? "复验中…" : "重新复验"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
