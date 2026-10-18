// 出处:人工构造(噪音:回读值作绑定参数——安全用法,弱锚不命中)
const rows = await db.query("SELECT * FROM t WHERE u = ?", [cfgRepo.findOne({ where: { id } }).value]);
