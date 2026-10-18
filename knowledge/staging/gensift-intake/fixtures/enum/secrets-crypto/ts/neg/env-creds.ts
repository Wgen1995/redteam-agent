// 出处:人工构造(硬负例:env 取值外部化)
const password = process.env.DB_PASSWORD;
const pool = mysql.createPool({ host, user, password });
