// 出处:人工构造(硬负例:回读值仅作绑定参数,无再拼接——C4 推翻形态)
const user = await userRepo.findOne({ where: { id } });
const rows = await db.query("SELECT * FROM t WHERE u = ?", [user.remark]);
