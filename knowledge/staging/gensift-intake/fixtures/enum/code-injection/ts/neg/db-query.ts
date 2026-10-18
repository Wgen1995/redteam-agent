// 出处:人工构造(硬负例:参数化查询)
const rows = await db.query("SELECT * FROM t WHERE id = ?", [id]);
