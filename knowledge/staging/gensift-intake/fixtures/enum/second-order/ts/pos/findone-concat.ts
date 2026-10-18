// 出处:人工构造(依据 CWE-89 二阶:sequelize findOne 回读存储值再拼接)
const sql = "SELECT * FROM mail_queue WHERE hdr = '" + (await cfgRepo.findOne({ where: { id } })).value + "'";
await db.query(sql);
