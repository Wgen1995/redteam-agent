// 出处:人工构造(噪音:占位符)
const [r] = await conn.execute("SELECT * FROM t WHERE v = ?", [v]);
