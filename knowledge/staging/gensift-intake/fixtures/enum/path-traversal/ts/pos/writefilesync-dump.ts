// 出处:人工构造(依据 CWE-22 同步写拼接形态)
fs.writeFileSync('/tmp/' + req.body.token + '.dat', blob);
