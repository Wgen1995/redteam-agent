// 出处:人工构造(依据 CWE-613/287 签发无 expiresIn——C3 证据缺口)
export function issueToken(user: User) {
  return jwt.sign({ sub: user.id }, SECRET);
}
