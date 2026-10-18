// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/scripts/sandbox-egress-proxy.mjs — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 1-40 ----
#!/usr/bin/env node
// apps/server/scripts/sandbox-egress-proxy.mjs（BO4b T3·egress 白名单代理——sidecar 形只读挂载进 node:22-slim 代理容器）
//
// 职责：容器引擎外联白名单的单点执行面。引擎容器跑在 per-run --internal 专用网络（出站全断·OrbStack
// 29.4.0 实证：DNS EAI_AGAIN/裸 IP ENETUNREACH——见回执 docs/superpowers/BO4B-T3-NETWORK-WHITELIST.md
// 路 a 证据表），唯一可达对端=本代理（同网 sidecar·双网形：internal 网〔引擎可达〕+bridge 网〔出站路由〕）。
// 引擎经 HTTPS_PROXY/HTTP_PROXY（标准代理 env·网络族平台键——ZZ_ 过滤面之外由 sandbox.ts 网络参数族
// 平台注入）指向本代理；本代理按 CONNECT 目标域名对 ZZ_EGRESS_ALLOWLIST 白名单判定：
//   ·命中（=entry 或 *.entry 子域）→隧道建立（net.connect 上游·上游解析走 sidecar 自身 DNS/hosts——
//     域名解析单源收归代理，引擎容器零 DNS）；
//   ·未命中/缺名单/非法形态 → 403 拒（fail-closed：ZZ_EGRESS_ALLOWLIST 缺席或空=全拒，非全放）。
// 证据协议（stdout 行·docker logs/测试消费）：ZL-EGRESS-PROXY LISTEN/DENY/ALLOW/UPSTREAM-ERR 前缀行。
// 端口面：仅 80/443（CONNECT 目标端口白名单——25/587 等非 web 出站恒拒）。明文 HTTP 绝对形（GET
// http://host/...）恒 403——SNI/TLS 面只放 CONNECT 隧道（白名单判定点=CONNECT Host，等价 SNI 判定面）。
// 生命周期：--rm 一次性·spawn 工厂 post-clean rm -f 收口（与 zl-sandbox-* 容器同律——容器名同前缀，
// startup 孤儿容器清扫 zl-sandbox-* 过滤面顺带覆盖崩溃遗留 sidecar）。
//
// 安全姿态（与 sandbox-wrap.mjs 同纪律）：零 shell（全 argv/socket API）·零依赖（node: 内建）·零凭据
// 经手（白名单=配置非秘密·inspect 可见面无敏感值）·解析器手写最小面（host:port 拆分+域形态校验——
// URL 解析器的宽接受面不引入）。
import http from 'node:http'
import net from 'node:net'

const PORT = Number(process.env.ZZ_EGRESS_PORT ?? '3128')
const TUNNEL_PORTS = new Set(['80', '443'])
// fail-closed：缺席/空/全非法项=空名单=全拒（白名单底座缺省姿态——不是缺省放行）
const ALLOWLIST = (process.env.ZZ_EGRESS_ALLOWLIST ?? '')
  .split(',')
  .map(s => s.trim().toLowerCase().replace(/\.+$/, ''))   // 归一：小写+尾点剥除
  .filter(s => /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$/.test(s))

// BO4b T3：静态主机映射（ZZ_EGRESS_HOST_MAP='host:port=ip:port,...'——离线/IP 钉部署面：容器引擎只可达
// 同网 sidecar 时，白名单内域名的上游解析收归编排面钉表——bridge-first sidecar 的宿主 resolv.conf 解析不了
// user-defined 网成员名[OrbStack 实证 ENOTFOUND]，映射表=域名白名单语义与 IP 直连两全的桥）。非法项剥除。
const HOST_MAP = new Map()
for (const entry of (process.env.ZZ_EGRESS_HOST_MAP ?? '').split(',')) {
  const i = entry.indexOf('=')
  if (i <= 0) continue
  const key = entry.slice(0, i).trim().toLowerCase()
  const val = entry.slice(i + 1).trim()
// ---- excerpt lines 70-82 ----
server.on('connect', (req, clientSocket, head) => {
  const target = parseTarget(req.url ?? '')
  if (target === null || !allowed(target.host)) {
    console.log('ZL-EGRESS-PROXY DENY ' + String(req.url) + ' (allowlist=' + ALLOWLIST.length + ')')
    // BO9 T2 RST 加固：DENY 后客户端 RST（引擎对 403 的 reset 处置形——T1 §5 实证 unhandled ECONNRESET
    // 即 sidecar exit 1=egress 单点灭）→error 监听先于 end 挂上·记证据行+优雅收·连接级失败不杀进程。
    clientSocket.once('error', e => {
      console.log('ZL-EGRESS-PROXY DENY-RESET ' + String(req.url) + ' ' + String(e?.code ?? 'error'))
      clientSocket.destroy()
    })
    clientSocket.end('HTTP/1.1 403 Forbidden\r\nconnection: close\r\n\r\n')   // end=刷出后断（destroy 有丢数据竞态）
    return
  }
