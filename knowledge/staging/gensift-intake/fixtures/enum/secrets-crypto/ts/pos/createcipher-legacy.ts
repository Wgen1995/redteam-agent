// 出处:人工构造(依据 CWE-327 node crypto 弃用 createCipher 家族)
const cipher = crypto.createCipher("aes-256-cbc", staticPassword);
const enc = Buffer.concat([cipher.update(plain), cipher.final()]);
