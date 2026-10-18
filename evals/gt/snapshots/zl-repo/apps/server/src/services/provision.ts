// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/provision.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 14-45 ----
export interface ProvisionTokenRow {
  id: number; token_hash: string; created_by: number; expires_at: number
  used_at: number | null; used_by_machine: string | null
  public_key_fingerprint: string | null; revoked_at: number | null; created_at: number
  remark: string | null   // 0013（BO3e T1a）：备注列（生成时可填·缺省 NULL）
}
export interface ProvisionListRow {
  id: number; createdAt: number; expiresAt: number
  usedAt: number | null; revokedAt: number | null; usedByMachine: string | null
  remark: string | null   // BO3e T1a：加性透出（旧行 null——旧消费方零改动）
}

export function hashProvisionToken(token: string): string {
  return createHash('sha256').update(token).digest('hex')
}

// 端点30：生成一次性令牌（admin only·闸在路由）。randomBytes(24) hex＝48 字符；明文仅此一次返回（①）。
// BO3e T1a：加性可选 remark（≤200 非空·契约 ProvisionCreateBodySchema——缺省不带=旧调用零改动）。
export function createProvisionToken(db: Db, adminId: number, now: number, remark?: string): { token: string; expiresAt: number } {
  const token = randomBytes(24).toString('hex')
  const expiresAt = now + PROVISION_TTL_SEC
  db.prepare('INSERT INTO provision_tokens (token_hash, created_by, expires_at, created_at, remark) VALUES (?, ?, ?, ?, ?)')
    .run(hashProvisionToken(token), adminId, expiresAt, now, remark ?? null)
  return { token, expiresAt }
}

// 端点73：列表（admin only）——全状态（活跃/已用/已吊销）·created_at DESC（同刻并列 id DESC 稳定序）。
export function listProvisionTokens(db: Db): ProvisionListRow[] {
  const rows = db.prepare('SELECT * FROM provision_tokens ORDER BY created_at DESC, id DESC').all() as ProvisionTokenRow[]
  return rows.map(r => ({ id: r.id, createdAt: r.created_at, expiresAt: r.expires_at, usedAt: r.used_at, revokedAt: r.revoked_at, usedByMachine: r.used_by_machine, remark: r.remark }))
}

// ---- excerpt lines 46-62 ----
// 端点72：吊销——已用令牌吊销无意义＝无操作果·重复吊销幂等（均 204）；不存在→404 同形（§5.2 防探测）。
export function revokeProvisionToken(db: Db, id: number, now: number): void {
  const row = db.prepare('SELECT id FROM provision_tokens WHERE id = ?').get(id)
  if (!row) throw new DomainError(404, 'E_NOT_FOUND', '资源不存在或不可见')   // 文案与全局 NOT_FOUND_BODY 逐字一致
  db.prepare('UPDATE provision_tokens SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL AND used_at IS NULL').run(now, id)
}

// T7 register 消费的读判定（纯函数）：{ok:row}｜{err:'expired'|'revoked'|'used'|'not_found'}。
// 判序＝③ 吊销→④ 已用→② 过期（§8.1 纪律次序：吊销先于过期；首用即焚先于过期）。
export type ProvisionValidation = { ok: ProvisionTokenRow } | { err: 'expired' | 'revoked' | 'used' | 'not_found' }

export function validateProvisionToken(db: Db, token: string, now: number = Math.floor(Date.now() / 1000)): ProvisionValidation {
  const row = db.prepare('SELECT * FROM provision_tokens WHERE token_hash = ?').get(hashProvisionToken(token)) as ProvisionTokenRow | undefined
  if (!row) return { err: 'not_found' }
  if (row.revoked_at !== null) return { err: 'revoked' }   // ③ 吊销即失效（先于过期）
  if (row.used_at !== null) return { err: 'used' }         // ④ 首用即焚（二次使用由 T7 转 409）
  if (row.expires_at <= now) return { err: 'expired' }     // ② 满 24h 即过期（含恰好到期）
