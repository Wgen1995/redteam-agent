// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/routes/runner.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 56-64 ----
export function runnerRouter(deps: AppDeps): Hono {
  const route = new Hono()
  // 端点50：注册（provision 一次性令牌首用即焚→资源行+资源令牌+sealedMasterKey）｜重连（machineId+旧资源令牌→沿用行发新令牌）
  route.post('/api/runner/register', async (c) => {
    try {
      const body = RegisterBodySchema.parse(await c.req.json())
      return c.json(await registerResource(deps.db, deps.cfg, body), 201)
    } catch (e) { return toErrorResponse(c, e) }
  })

// ---- excerpt lines 112-134 ----
  route.post('/api/runner/claim', async (c) => {
    try {
      const now = Math.floor(Date.now() / 1000)
      const body = ClaimBodySchema.parse(await c.req.json())
      const auth = authenticateResource(deps.db, body.resourceToken)
      if (!auth || auth.row.id !== body.resourceId)
        throw new DomainError(401, 'E_UNAUTHORIZED', '资源令牌无效或已失效')
      requireActiveResource(auth)   // R-C1：停用即时 403（§8.1-7——先于 prev 坍缩/领任务）
      if (auth.row.token_hash_prev !== null)   // T11 统一：prev 非 NULL 即清（T10 heartbeat 同款——新令牌首认也坍缩）
        deps.db.prepare('UPDATE asset_resources SET token_hash_prev = NULL, updated_at = ? WHERE id = ?').run(now, auth.row.id)
      // ([187]#7) claim 200 捎带下行命令：commands 为契约外字段（heartbeat 响应 commands 同名同形先例）——
      // claim 15s 轮询与心跳 30s 并行下行·cancel/kill 延迟半程（30s→15s）；空手领取（task:null）同车下发
      // （对账 kill 的幽灵资源常满槽/不可领——命令通道不因领不到任务而断）。取走即清队（takeCommands 语义）。
      return c.json({
        ...claimTask(
          { db: deps.db, cfg: deps.cfg, logger: deps.logger },
          { resourceId: body.resourceId, supportedClis: body.supportedClis, protocolCaps: body.protocolCaps },
          now,
        ),
        commands: takeCommands(body.resourceId),
      }, 200)
    } catch (e) { return toErrorResponse(c, e) }
  })
