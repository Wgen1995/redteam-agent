// 出处:人工构造(依据 CWE-918 axios GET 形态)
export async function loadRemote(targetUrl: string) {
  const { data } = await axios.get(targetUrl, { timeout: 3000 });
  return data;
}
