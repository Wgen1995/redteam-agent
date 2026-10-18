// 出处:人工构造(依据 CWE-601 location.assign 导航)
export function ssoExit(relay: string) {
  location.assign(relay);
}
