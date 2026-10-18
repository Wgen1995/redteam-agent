// 出处:人工构造(依据 CWE-287 remember-me 令牌可预测派生)
export function rememberMeToken(res: Response, user: User) {
  const token = `${user.id}:${Date.now()}`;
  res.cookie("rememberMe", token, { maxAge: 31536000000 });
  return token;
}
