// 出处:人工构造(硬负例:JWT 验签是认证非授权)
export function verifyAccess(token: string) {
  const payload = jwt.verify(token, publicKey, { algorithms: ["RS256"] });
  return payload.sub !== undefined;
}
