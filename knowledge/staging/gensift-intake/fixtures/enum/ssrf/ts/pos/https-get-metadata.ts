// 出处:人工构造(依据 CWE-918 https.get 云 metadata 形态)
import * as https from 'https';
export function readMetadata(path: string, cb: (b: string) => void) {
  https.get(`http://169.254.169.254/latest/meta-data/${path}`, (res) => {
    let body = '';
    res.on('data', (c) => (body += c));
    res.on('end', () => cb(body));
  });
}
