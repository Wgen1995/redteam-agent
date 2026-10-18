// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/password.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 1-14 ----
// apps/server/src/services/password.ts
// scrypt（N=16384,r=8,p=1）加盐哈希（§5.1）；会话令牌 256 位随机、库存 sha256。
import { createHash, randomBytes, scryptSync, timingSafeEqual } from 'node:crypto'

const SCRYPT = { N: 16384, r: 8, p: 1, keylen: 64 }

export function hashPassword(plain: string): string {
  const salt = randomBytes(16)
  const hash = scryptSync(plain, salt, SCRYPT.keylen, { N: SCRYPT.N, r: SCRYPT.r, p: SCRYPT.p })
  return ['scrypt', SCRYPT.N, SCRYPT.r, SCRYPT.p, salt.toString('base64'), hash.toString('base64')].join('$')
}

export function verifyPassword(plain: string, stored: string): boolean {
  const parts = stored.split('$')
