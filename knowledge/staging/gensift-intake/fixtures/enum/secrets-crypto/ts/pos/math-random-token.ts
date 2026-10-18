// 出处:人工构造(依据 CWE-330/327 弱随机令牌)
function makeToken(): string {
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
}
