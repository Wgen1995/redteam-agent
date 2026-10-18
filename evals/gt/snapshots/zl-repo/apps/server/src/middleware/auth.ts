// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) apps/server/src/middleware/auth.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 1-35 ----
// apps/server/src/middleware/auth.ts
// 每请求中间件（§5.1）：解 Cookie→查会话→无效 401 E_UNAUTHORIZED→前端跳 /login?redirect=。
// 响应后滑动续期（60s 写节流）。
import { createMiddleware } from 'hono/factory'
import { getCookie } from 'hono/cookie'
import { apiErrorBody } from '@zhulong/contracts'
import type { AppDeps } from '../app'
import { resolveSession, touchSession, type UserRow } from '../services/sessions'
import { usersEmpty } from '../services/auth'
import { setAuthCookie } from './auth-cookie'

export interface AuthEnv {
  Variables: { user: UserRow; userId: number }
}

export function authMiddleware(deps: AppDeps) {
  return createMiddleware<AuthEnv>(async (c, next) => {
    const token = getCookie(c, 'zl_sess')
    const now = Math.floor(Date.now() / 1000)
    const resolved = token ? resolveSession(deps.db, token, now) : null
    if (!resolved) {
      const details = usersEmpty(deps.db) ? { setupNeeded: true } : undefined
      return c.json(apiErrorBody('E_UNAUTHORIZED', '未认证或会话失效', details), 401)
    }
    c.set('user', resolved.user)
    c.set('userId', resolved.user.id)
    await next()
    // 7 天滑动：每请求续期 last_seen，60s 写节流（§5.1）；续期命中时重发同属性 Set-Cookie，
    // 使浏览器侧 maxAge 同步滑动（否则第 7 天浏览器绝对过期踢出，DB 续期永不生效——终评审 I-4）
    const renewed = touchSession(deps.db, resolved.session.id, now, deps.cfg.sessionWriteThrottleSec, deps.cfg.sessionTtlDays)
    if (renewed && token) setAuthCookie(c, token, deps.cfg.sessionTtlDays)
  })
}

