// 出处:人工构造(依据 CWE-89 二阶:写侧入库,另一请求 typeorm findByX 回读再拼 SQL)
router.put("/profile", async (req, res) => { await userRepo.save(req.body); });

const sql = "SELECT * FROM audit WHERE note = '" + (await userRepo.findByName(name)).remark + "'";
await db.query(sql);
