// 出处:人工构造(CWE-89 knex fromRaw)
const q = knex.select("*").fromRaw("t WHERE flag = '" + flag + "'");
