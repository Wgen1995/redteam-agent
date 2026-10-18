// 出处:人工构造(依据 CWE-89 二阶:redis 会话回读再拼接)
const sql = "SELECT * FROM sess WHERE k = '" + (await redis.get(sid)) + "'";
await db.query(sql);
