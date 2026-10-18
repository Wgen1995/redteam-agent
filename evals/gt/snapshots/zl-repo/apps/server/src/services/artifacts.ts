// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/artifacts.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 85-95 ----
// 单段名防穿越（§5.4 同源收平）：basename 收平后须与原值一致（'../x'、'a/b'、'..' 均拒）——stageKey/filename
// 是落盘路径段，不允许目录结构。BO3e T2 导出：分片径（artifact-chunks）临时面键同律复用。
export function safeSegment(name: string, what: string): string {
  if (name === '' || name === '.' || name === '..' || name !== path.basename(name) || /[/\\]/.test(name))
    throw new DomainError(400, 'E_INVALID_PARAMS', what + ' 不是合法的单段名称')
  return name
}

const B64_RE = /^[A-Za-z0-9+/]*={0,2}$/
export function decodeBase64(s: string): Buffer {
  const t = s.replace(/\s+/g, '')
// ---- excerpt lines 148-156 ----
  // 恶意 runner（绕过收集面）在此复检（解码缓冲已在内存·memchr 行扫描廉价·拒绝＝零落盘）。
  // BO3e T2 sourcePath 分支：分片拼装件（临时面磁盘件）——hashArtifactFile 流式哈希+行长扫描
  // （T10 守卫同律·500MB 级件不整读进内存）；总哈希终验在此统一（complete 面不重复读全文）。
  const decoded = input.files.map(f => {
    const filename = safeSegment(f.filename, 'filename')
    if (f.sourcePath !== undefined) {
      let collected: { sha256: string; size: number }
      try { collected = hashArtifactFile(f.sourcePath, filename) }
      catch (err) { throw new DomainError(400, 'E_INVALID_PARAMS', (err as Error).message) }
