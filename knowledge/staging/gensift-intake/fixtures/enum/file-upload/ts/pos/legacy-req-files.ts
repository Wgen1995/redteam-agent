// 出处:人工构造(依据 CWE-434 express4 前遗留 req.files 挂载点形态)
import * as fs from 'fs';
module.exports = function (req: any, res: any) {
  const avatar = req.files.avatar;
  fs.writeFile('uploads/' + avatar.name, avatar.data, () => res.end('ok'));
};
