// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/artifact-chunks.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 40-50 ----

/** 端点80：单片落键目录（幂等＝同序号覆写）。体上限＝MAX_ARTIFACT_LINE_BYTES 同律（解码后强校验——
 *  契约层无法表达解码后界）。返回实收字节数（发送面观测）。 */
export function writeArtifactChunk(deps: ArtifactsDeps, input: ArtifactChunkInput): { bytes: number } {
  const stageKey = safeSegment(input.stageKey, 'stageKey')
  const filename = safeSegment(input.filename, 'filename')
  const buf = decodeBase64(input.contentBase64)
  if (buf.length > MAX_ARTIFACT_LINE_BYTES)
    throw new DomainError(400, 'E_INVALID_PARAMS',
      '分片体超过上限（' + filename + ' 第 ' + input.index + ' 片解码后 ' + buf.length + ' 字节 > 上限 ' + MAX_ARTIFACT_LINE_BYTES +
      ' 字节（16 MiB）——分片体上限=产物单行上限同律（MAX_ARTIFACT_LINE_BYTES 单源））')
