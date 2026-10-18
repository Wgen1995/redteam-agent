// 出处:人工构造(CWE-89 mysql2)
const [rows] = await conn.execute("SELECT * FROM t WHERE id=" + req.query.id);
