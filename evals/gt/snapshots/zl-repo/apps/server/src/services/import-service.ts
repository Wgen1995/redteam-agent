// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/services/import-service.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 88-100 ----
  if (body.engineId !== 'zhulong')
    throw new DomainError(400, 'E_INVALID_PARAMS', '引擎暂无导入映射器（当前仅 zhulong）：' + body.engineId, 'import.invalid', { engineId: body.engineId })
  // ①目录校验（§2.4）：存在＋目录＋条目上限
  if (!existsSync(body.sourceDir) || !statSync(body.sourceDir).isDirectory())
    throw new DomainError(400, 'E_INVALID_PARAMS', '会话目录不存在', 'import.invalid')
  const files = readdirSync(body.sourceDir).sort()
  if (files.length > IMPORT_FILE_LIMIT)
    throw new DomainError(400, 'E_INVALID_PARAMS', '目录条目 ' + files.length + ' 超上限 ' + IMPORT_FILE_LIMIT + '，请拆分后导入', 'import.invalid')
  // ②artifactSpec 核心文件（引擎快照 output.artifacts required pattern 须有命中；缺→400＋清单）
  const manifest = BUILTIN_ENGINE_MANIFESTS.find(m => m.id === body.engineId)
  if (!manifest) throw new DomainError(400, 'E_INVALID_PARAMS', '未知引擎：' + body.engineId, 'import.invalid')
  const missing: string[] = []
  for (const a of manifest.output.artifacts.filter(x => x.required)) {
// ---- excerpt lines 110-140 ----
  // ④读文件（.md 全量＝产物原文；非 md 条目仅计入批次清单）
  const mdFiles = files.filter(f => f.endsWith('.md'))
  const contents: Record<string, string> = {}
  for (const f of mdFiles) contents[f] = readFileSync(path.join(body.sourceDir, f), 'utf8')
  const runId = 'imp-' + now + '-' + Math.random().toString(36).slice(2, 8)
  let taskDir: string | null = null   // 事务内建目录的清理锚点（失败即扫——无半批文件残迹）

  // ⑤映射＋T3 单事务（task＋artifacts＋findings＋batch 全或无）；mapper 在 try 内——崩溃同样落失败批次行
  try {
    const mapped = mapper(contents)
    return deps.db.transaction((): ImportResult => {
      const stageSnapshot = mapped.stages.map(s => ({ word: s.file.replace(/\.md$/, ''), display: s.word, status: 'done' as const }))
      const tInfo = deps.db.prepare(
        'INSERT INTO tasks (project_id, created_by, engine_id, engine_version, mode, target_object_id, target_env_id, resource_id, params, origin, status, current_run_id, harness_session, stage_snapshot, progress, error, started_at, finished_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?, NULL, ?, ?, ?, ?)',
      ).run(body.projectId, user.id, body.engineId, manifest.version, '开眼',
        body.objectId ?? null, body.envId ?? null,
        JSON.stringify({ sourceDir: body.sourceDir, importedAt: now }),
        'import', 'success', runId,
        JSON.stringify(stageSnapshot), JSON.stringify({ done: stageSnapshot.length, total: stageSnapshot.length }),
        now, now, now, now)
      const taskId = Number(tInfo.lastInsertRowid)
      // 产物原文永久留存（§3.6：拷入 tasks/<id>/runs/<runId>/workspace/＋sha256）
      const workspace = path.resolve(deps.dataDir, 'tasks', String(taskId), 'runs', runId, 'workspace')
      taskDir = path.resolve(deps.dataDir, 'tasks', String(taskId))
      mkdirSync(workspace, { recursive: true })
      let artifactCount = 0
      for (const f of mdFiles) {
        copyFileSync(path.join(body.sourceDir, f), path.join(workspace, f))
        const buf = readFileSync(path.join(body.sourceDir, f))
        deps.db.prepare('INSERT INTO artifacts (task_id, run_id, stage_key, filename, path, sha256, size, mtime) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
          .run(taskId, runId, f.split('-')[0], f, path.join(workspace, f), createHash('sha256').update(buf).digest('hex'), buf.length, now)
