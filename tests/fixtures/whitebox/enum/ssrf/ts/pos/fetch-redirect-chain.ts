// 出处:人工构造(依据 CWE-918 模板串拼接 + redirect follow 形态)
export async function resolve(base: string, path: string) {
  const res = await fetch(`${base}/${path}`, { redirect: 'follow' });
  return res.url;
}
