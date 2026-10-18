// 出处:人工构造(依据 CWE-330/287 Math.random 弱熵源令牌)
export function passwordResetToken(email: string) {
  const token = Math.random().toString(36).slice(2);
  store.set(token, email);
  return token;
}
