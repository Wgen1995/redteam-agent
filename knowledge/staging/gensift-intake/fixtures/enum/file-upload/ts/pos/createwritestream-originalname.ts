// 出处:人工构造(依据 CWE-434 createWriteStream 流式落盘原名)
import * as fs from 'fs';
export function streamOut(file: Express.Multer.File) {
  const out = fs.createWriteStream(file.originalname, { flags: 'w' });
  out.write(file.buffer);
  out.end();
}
