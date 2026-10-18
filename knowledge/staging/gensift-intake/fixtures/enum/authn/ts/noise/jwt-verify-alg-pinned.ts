// 出处:人工构造(噪音:钉死算法族的验签)
export function checkToken(token: string) {
  return jwt.verify(token, publicKey, { algorithms: ["RS256"] });
}
