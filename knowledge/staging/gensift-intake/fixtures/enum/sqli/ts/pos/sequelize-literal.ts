// 出处:人工构造(CWE-89 sequelize literal)
q.where(sequelize.literal("name = '" + name + "'"));
