// 出处:人工构造(依据 CWE-613 超长有效期签发)
export function issueToken(user: User) {
  return jwt.sign({ sub: user.id }, SECRET, { expiresIn: "365d" });
}
