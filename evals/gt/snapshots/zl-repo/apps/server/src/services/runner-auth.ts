// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/runner-auth.ts — regen: evals/gt/README.md §快照纪律
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
