// 出处:人工构造(CWE-89 pg)
const res = await client.query("UPDATE t SET v='" + v + "' WHERE id=" + id);
