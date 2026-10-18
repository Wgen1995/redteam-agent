// 出处:人工构造(噪音:常量 raw)
const now = await knex.raw("SELECT NOW()");
