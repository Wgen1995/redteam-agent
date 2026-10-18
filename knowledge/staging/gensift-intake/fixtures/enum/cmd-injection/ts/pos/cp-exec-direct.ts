// 出处:人工构造(require 直连命名空间形态)
const cp = require('child_process');
cp.exec('unzip -o ' + uploadedName + ' -d /tmp/x', cb);
