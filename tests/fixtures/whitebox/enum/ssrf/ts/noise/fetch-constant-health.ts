// 出处:人工构造(噪音:同 API 安全用法——常量 URL,允许命中)
export async function health() {
  const res = await fetch('http://localhost:9110/health');
  return res.status === 200;
}
