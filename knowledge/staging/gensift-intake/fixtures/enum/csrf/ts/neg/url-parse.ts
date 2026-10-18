// 出处:人工构造(硬负例:URL 解析比较,无跳转)
export function isInternalAsset(input: string): boolean {
  const parsed = new URL(input, "https://cdn.example.com");
  return parsed.hostname === "cdn.example.com";
}
