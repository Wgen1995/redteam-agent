// 出处:人工构造(CWE-89 sequelize raw 拼接)
const users = await sequelize.query(`SELECT * FROM users WHERE name = '${name}'`);
