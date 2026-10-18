// 出处:人工构造(依据 CWE-798 对象字面量口令)
const dbConfig = { host: "db.internal", user: "app", password: "Sup3rS3cret!" };
await mysql.createConnection(dbConfig);
