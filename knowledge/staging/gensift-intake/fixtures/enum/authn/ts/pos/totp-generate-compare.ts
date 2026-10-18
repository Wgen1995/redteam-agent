// 出处:人工构造(依据 CWE-287 自比对 TOTP,无窗口与限次)
export function verifyMfa(secret: string, code: string) {
  return totp.generate(secret) === code;
}
