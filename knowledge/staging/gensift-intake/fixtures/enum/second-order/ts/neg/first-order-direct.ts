// 出处:人工构造(硬负例:同请求直达无存储中介——归 sqli 类,C1 反例形态)
const sql = "SELECT * FROM users WHERE name = '" + req.query.name + "'";
await db.query(sql);
