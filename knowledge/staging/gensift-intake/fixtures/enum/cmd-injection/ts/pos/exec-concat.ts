// 出处:人工构造(依据 CWE-78 child_process.exec 拼接)
const { exec } = require('child_process');
exec('tail -n 100 ' + req.query.file, callback);
