// 出处:人工构造(CWE-89 knex)
const r = await knex.raw("SELECT * FROM t WHERE id = " + id);
