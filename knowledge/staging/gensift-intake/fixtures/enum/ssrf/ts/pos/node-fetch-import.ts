// 出处:人工构造(依据 CWE-918 node-fetch 导入形态)
import fetch from 'node-fetch';
export async function openNext(nextUrl: string) {
  const res = await fetch(nextUrl, { redirect: 'manual' });
  return res.headers.get('location');
}
