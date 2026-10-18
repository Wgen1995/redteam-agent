// 出处:人工构造(依据 CWE-89 二阶:模板字符串内联回读——TS 次级载体)
const q = `SELECT * FROM cfg WHERE v = '${await userCache.get(key)}'`;
await db.query(q);
