// 出处:人工构造(动态 import 形态)
const { exec } = await import('child_process');
exec('openssl x509 -in ' + certPath + ' -noout -text', cb);
