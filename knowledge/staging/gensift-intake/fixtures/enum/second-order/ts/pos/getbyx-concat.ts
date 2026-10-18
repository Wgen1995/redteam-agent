// 出处:人工构造(依据 CWE-89 二阶:配置服务 getBySlug 回读再拼接)
const q = "UPDATE tags SET label = '" + configService.getBySlug(slug).label + "'";
await db.execute(q);
