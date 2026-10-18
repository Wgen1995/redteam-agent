// 出处:人工构造(依据 CWE-918 got 形态)
import got from 'got';
export async function pull(url: string) {
  const body = await got(url).text();
  return body.slice(0, 512);
}
