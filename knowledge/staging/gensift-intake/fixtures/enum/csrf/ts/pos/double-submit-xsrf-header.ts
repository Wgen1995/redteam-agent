// 出处:人工构造(依据 CWE-352 双提交回发链——cookie 侧可被子域种入,C-g 材料)
export function attachCsrf(cookies: Record<string, string>) {
  const token = cookies["XSRF-TOKEN"];
  return { "X-XSRF-TOKEN": token };
}
