// 出处:人工构造(CWE-89 自定义 DAO querySql)
const rows = dao.querySql("SELECT * FROM t WHERE id = " + id);
