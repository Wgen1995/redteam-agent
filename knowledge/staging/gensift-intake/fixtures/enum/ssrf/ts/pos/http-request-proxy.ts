// 出处:人工构造(依据 CWE-918 node http.request 流式代理形态)
import * as http from 'http';
export function pipeTo(req: http.IncomingMessage, target: string, res: http.ServerResponse) {
  const upstream = http.request(target, (upRes) => {
    res.writeHead(upRes.statusCode || 502);
    upRes.pipe(res);
  });
  req.pipe(upstream);
}
