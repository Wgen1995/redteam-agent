// 出处:人工构造(依据 CWE-347/287 verify 未钉算法族)
export function checkToken(token: string) {
  try {
    jwt.verify(token, SECRET);
    return true;
  } catch {
    return false;
  }
}
