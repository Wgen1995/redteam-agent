// 出处:人工构造(依据 CWE-434 writeFileSync 同步直写原名)
import * as fs from 'fs';
export function saveTmp(file: Express.Multer.File) {
  fs.writeFileSync('/var/www/html/assets/' + file.originalname, file.buffer);
}
