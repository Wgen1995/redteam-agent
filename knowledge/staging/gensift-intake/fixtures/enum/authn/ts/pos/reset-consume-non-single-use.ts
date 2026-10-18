// 出处:人工构造(依据 CWE-287/613 重置令牌用后不焚)
export async function applyReset(resetToken: string, newPassword: string) {
  const userId = tokenCache.get(resetToken);
  await users.resetPassword(resetToken, newPassword);
  return userId;
}
