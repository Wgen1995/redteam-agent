// 出处:人工构造(依据 CWE-434 fs.writeFile + 客户端文件名同行直拼)
import * as fs from 'fs';
import * as path from 'path';
export function persist(file: Express.Multer.File) {
  fs.writeFile(path.join('/srv/webapp/static', file.originalname), file.buffer, (err) => {
    if (err) logger.warn('write failed');
  });
}
