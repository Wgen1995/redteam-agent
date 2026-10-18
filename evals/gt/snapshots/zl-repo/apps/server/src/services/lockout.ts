// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/lockout.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 1-22 ----
// apps/server/src/services/lockout.ts（整体替换任务7骨架）
// 登录失败锁定（§5.1：连续失败锁定 5 次/15 分）。
// 内存实现依据：ADR-1 单机单进程；重启清零（spec 未要求持久化，内网可接受）。
export interface LoginLockout {
  remainingSec(username: string, now: number): number
  recordFailure(username: string, now: number): void
  recordSuccess(username: string): void
}

export function createLoginLockout(maxAttempts: number, windowSec: number): LoginLockout {
  const state = new Map<string, { count: number; windowEnd: number; lockedUntil: number }>()
  return {
    remainingSec(username, now) {
      const s = state.get(username)
      if (!s) return 0
      if (s.lockedUntil > now) return s.lockedUntil - now
      if (s.windowEnd <= now) state.delete(username)     // 计数窗口滑过→清零
      return 0
    },
    recordFailure(username, now) {
      const prev = state.get(username)
      const s = prev && prev.windowEnd > now && prev.lockedUntil <= now
