// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/assets.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 472-503 ----
// ——T1-18 A3 过渡性 SSRF 闸（裁定：仅禁下述类别，完整出口白名单属 BO3）——
// 拒：环回（127/8·::1·localhost）、链路本地（169.254/16 含云元数据 169.254.169.254·fe80::/10）、
// 0.0.0.0/8 IP 字面量（IPv6 未指定 :: 同拒）、云元数据主机名（GCP/Azure/EC2）。
// 放行：RFC1918（10/8·172.16/12·192.168/16）——本平台合法探活内网 runner。
// 已记录局限：非 IP 主机名解析到私网地址不在此闸（逐请求 DNS 解析代价高·URL 归一已覆盖 IP 字面量变体）。
const CLOUD_METADATA_HOSTS = new Set(['metadata.google.internal', 'metadata.azure.com', 'instance-data'])

// 返回禁用类别（作 details.reason）或 null（放行）；URL 解析失败交由 fetch 失败→unreachable（原语义）
export function forbiddenHealthHost(endpoint: string): string | null {
  let hostname: string
  try { hostname = new URL(endpoint).hostname.toLowerCase() } catch { return null }
  if (hostname.startsWith('[') && hostname.endsWith(']')) hostname = hostname.slice(1, -1)   // URL hostname 对 IPv6 保留方括号
  if (hostname.endsWith('.')) hostname = hostname.slice(0, -1)   // FW-9d：尾点绝对 FQDN（'localhost.'）DNS 解析同主机——剥后同类别判
  if (hostname === 'localhost' || hostname === '::1') return 'loopback'
  if (hostname === '::') return 'unspecified'
  if (CLOUD_METADATA_HOSTS.has(hostname)) return 'metadata'
  const ipv4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(hostname)   // URL 已归一十六/八进制/短式写法
  if (ipv4) {
    const a = Number(ipv4[1]); const b = Number(ipv4[2])
    if (a === 127) return 'loopback'
    if (a === 169 && b === 254) return 'link-local'
    if (a === 0) return 'unspecified'
    return null   // 含 RFC1918 放行（内网 runner 合法探活）
  }
  if (hostname.includes(':')) {   // 其余 IPv6 字面量（URL 把 IPv4 映射式归一为十六进制 hextet，如 ::ffff:7f00:1）
    if (/^fe[89ab][0-9a-f]$/.test(hostname.split(':')[0])) return 'link-local'   // fe80::/10
    const mapped = /^::ffff:([0-9a-f]{1,4}):([0-9a-f]{1,4})$/.exec(hostname)   // ::ffff:a.b.c.d——按同类别判
    if (mapped) {
      const a = parseInt(mapped[1], 16) >> 8; const b = parseInt(mapped[1], 16) & 0xff   // 首两字节＝a.b
      if (a === 127) return 'loopback'
      if (a === 169 && b === 254) return 'link-local'
      if (a === 0) return 'unspecified'
// ---- excerpt lines 505-512 ----
  }
  return null   // 普通主机名：本闸不做 DNS 解析（局限见上注）
}

export async function healthCheckEnvironment(db: Db, actor: AuthUser, id: number, now: number): Promise<{ ok: boolean; fingerprint: Record<string, unknown> | null; checkedAt: number }> {
  const row = requireEnvOwner(db, actor, id)   // 探活＝写操作：owner/admin（权限矩阵端点 41 列）·他人 404 同形
  requireAssetWriter(db, actor)                 // RBAC-1：资产写能力门
  let ok = false; let fingerprint: Record<string, unknown> | null = null
// ---- excerpt lines 316-324 ----
// 端点35：上传＝staging→<dataDir>/objects/<id>/<version>/<filename>＋sha256 回写（§3.6 登记/上传解耦：
// 登记即 v1 预留，上传自 v2 起；version＝该对象已有版本目录最大号+1，版本目录即上传历史）

// 上传大小上限（§3.6 上传校验·T1-18 A1 裁定值 100MB）：app 级 bodyLimit 与路由 file.size 闸共用的单一出处
export const MAX_UPLOAD_BYTES = 100 * 1024 * 1024

export function saveUpload(db: Db, dataDir: string, actor: AuthUser, id: number, staging: { path: string; filename: string; sha256?: string; size?: number }, now: number): { sha256: string; size: number } {
  requireObjectOwner(db, actor, id)   // 上传＝写操作：owner/admin（权限矩阵端点 35 列）
  requireAssetWriter(db, actor)       // RBAC-1：资产写能力门
