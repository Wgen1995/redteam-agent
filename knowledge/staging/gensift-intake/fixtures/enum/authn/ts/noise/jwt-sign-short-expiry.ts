// 出处:人工构造(噪音:短有效期签发)
export function issueToken(user: User) {
  return jwt.sign({ sub: user.id }, SECRET, { expiresIn: "15m" });
}
