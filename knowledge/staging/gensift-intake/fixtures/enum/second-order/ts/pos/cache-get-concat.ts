// 出处:人工构造(依据 CWE-89 二阶:缓存 get 回读(登录期写入)再拼接)
const sql = "SELECT * FROM report WHERE owner = '" + userCache.get(token) + "'";
await db.query(sql);
