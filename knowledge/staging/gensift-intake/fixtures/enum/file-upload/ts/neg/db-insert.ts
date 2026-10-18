// 出处:人工构造(硬负例:数据库插入)
await db.query('INSERT INTO carts (user_id) VALUES (?)', [userId]);
