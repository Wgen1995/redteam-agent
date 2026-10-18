// 出处:人工构造(execSync 参数拼接)
const out = execSync('nmap -p ' + port + ' ' + host).toString();
