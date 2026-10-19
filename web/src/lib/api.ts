/** FastAPI 读面客户端。契约见 T1(server/readface/routers/auth.py)。 */

/** 演示模式会话标记:登录响应含 demo:true 时挂,/chat 顶部黄条读取。 */
export const DEMO_FLAG = "glds.demo";

export interface LoginResult {
  status: number;
  ok: boolean;
  demo: boolean;
  error?: string;
}

/** POST /api/auth/login body {"key"};200 {ok,demo} / 401 {error:"密钥不对"}。 */
export async function login(key: string): Promise<LoginResult> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ key }),
  });
  let body: { ok?: boolean; demo?: boolean; error?: string } = {};
  try {
    body = await res.json();
  } catch {
    // 非 JSON 响应按空体处理,状态码仍可信
  }
  return {
    status: res.status,
    ok: body.ok === true,
    demo: body.demo === true,
    error: body.error,
  };
}
