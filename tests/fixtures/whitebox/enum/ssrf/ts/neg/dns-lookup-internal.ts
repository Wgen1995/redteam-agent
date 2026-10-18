// 出处:人工构造(硬负例:DNS 解析属独立侦察面,非本类 HTTP 外发 sink)
import * as dns from 'dns';
export function resolveHost(name: string) {
  return dns.promises.resolve(name);
}
