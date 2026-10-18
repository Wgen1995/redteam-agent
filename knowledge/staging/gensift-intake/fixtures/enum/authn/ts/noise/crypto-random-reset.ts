// 出处:人工构造(噪音:randomBytes 令牌+短时效+一次性)
import { randomBytes } from "crypto";
export async function applyReset(resetToken: string, newPassword: string) {
  const entry = await store.consume(resetToken, { maxAgeMs: 15 * 60_000 });
  if (!entry) throw new Error("expired token");
  await users.resetPassword(resetToken, newPassword);
}
