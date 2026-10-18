// 出处:人工构造(依据 CWE-434 工具类封装形态)
import * as fs from 'fs';
import * as path from 'path';
export function saveUpload(file: Express.Multer.File, baseDir: string): string {
  fs.writeFile(path.join(baseDir, file.originalname), file.buffer, () => {});
  return path.join(baseDir, file.originalname);
}
