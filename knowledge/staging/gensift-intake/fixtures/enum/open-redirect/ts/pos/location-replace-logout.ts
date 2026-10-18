// 出处:人工构造(依据 CWE-601 location.replace 导航)
export function loggedOut(nextUrl: string) {
  location.replace(nextUrl);
}
