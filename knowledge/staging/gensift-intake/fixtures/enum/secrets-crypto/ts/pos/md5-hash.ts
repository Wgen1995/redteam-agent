// 出处:人工构造(依据 CWE-327 node crypto MD5 口令哈希)
const hashed = crypto.createHash("md5").update(password).digest("hex");
await db.storeUserHash(email, hashed);
