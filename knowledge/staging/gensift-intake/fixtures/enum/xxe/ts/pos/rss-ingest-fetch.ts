// 出处:人工构造(依据 CWE-611 外源 RSS 拉取解析——Ingress 侧不可信来源)
import { parseStringPromise } from 'xml2js';
export async function pullFeed(url: string) {
  const resp = await fetch(url);
  const xml = await resp.text();
  return parseStringPromise(xml);
}
