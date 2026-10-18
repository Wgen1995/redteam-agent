// 出处:人工构造(噪音:MD5 作缓存键——允许命中)
const cacheKey = crypto.createHash("md5").update(query).digest("hex");
