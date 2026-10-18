// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/runner-auth.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 42-50 ----
export interface RegisterResult {
  resourceId: number
  resourceToken: string
  pollIntervalSec: 15
  heartbeatIntervalSec: 30
  sealedMasterKey: string
  concurrency: number                       // T10 通告（契约外字段·D3 资源行同源列）——daemon 多 run 上限源（缺省 1）
}


// ---- excerpt lines 60-72 ----
  const fromBase64 = (b64: string, origin: string): Buffer => {
    const key = Buffer.from(b64.trim(), 'base64')
    if (key.length !== 32) throw new Error('主密钥应为 base64 编码的 32 字节：' + origin)
    return key
  }
  const envB64 = env[cfg.credentialKeyRef]
  if (envB64 !== undefined && envB64 !== '') return fromBase64(envB64, 'env ' + cfg.credentialKeyRef)
  const file = path.join(cfg.dataDir, 'credentials', 'master.key')
  if (existsSync(file)) return fromBase64(readFileSync(file, 'utf8'), file)
  const key = randomBytes(32)   // 首启自动生成（测试用临时 dataDir 自然隔离）
  mkdirSync(path.dirname(file), { recursive: true })
  writeFileSync(file, key.toString('base64') + '\n', { mode: 0o600 })
  chmodSync(file, 0o600)       // 显式收口（writeFileSync mode 仅建文件时生效·不受 umask 影响）

// ---- excerpt lines 76-107 ----
// NaCl sealed box（R11）：node:crypto 无 box seal——libsodium-wrappers（纯 wasm）crypto_box_seal。
export async function sealBytes(plain: Buffer, publicKey: Buffer): Promise<string> {
  await sodium.ready
  return Buffer.from(sodium.crypto_box_seal(plain, publicKey)).toString('base64')
}

function parsePublicKey(publicKey: string): Buffer {
  const pk = Buffer.from(publicKey, 'base64')
  if (pk.length !== 32) throw new DomainError(400, 'E_INVALID_PARAMS', 'publicKey 应为 base64 编码的 32 字节 X25519 公钥')
  return pk
}

// 资源令牌认证（T9-T12 消费面）：token_hash 命中＝现行令牌；token_hash_prev 命中＝轮换重叠期旧令牌
// （staleToken:true 供 T10 收口——新令牌首次成功后清 prev）。
export interface ResourceAuth { row: AssetResourceRow; staleToken: boolean }
export function authenticateResource(db: Db, token: string): ResourceAuth | null {
  const h = sha256Hex(token)
  const cur = db.prepare('SELECT * FROM asset_resources WHERE token_hash = ?').get(h) as AssetResourceRow | undefined
  if (cur) return { row: cur, staleToken: false }
  const prev = db.prepare('SELECT * FROM asset_resources WHERE token_hash_prev = ?').get(h) as AssetResourceRow | undefined
  if (prev) return { row: prev, staleToken: true }
  return null
}

// 双径同形出参：masterKey 已在上游解析校验（评审修复2：先于任何库变更）——此处只封密（sealed box）。
// T10：响应通告资源行 concurrency（scheduler 闸门①同源列·D3 缺省 1 可设 2）——daemon 侧 runs Map 上限源。
async function finish(resourceId: number, resourceToken: string, concurrency: number, masterKey: Buffer, pk: Buffer): Promise<RegisterResult> {
  return {
    resourceId, resourceToken, pollIntervalSec: 15, heartbeatIntervalSec: 30, concurrency,
    sealedMasterKey: await sealBytes(masterKey, pk),
  }
}
