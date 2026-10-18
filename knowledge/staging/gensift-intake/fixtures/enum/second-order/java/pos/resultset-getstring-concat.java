// 出处:人工构造(依据 CWE-89 二阶:ResultSet.getString 回读存储列再拼下一条 SQL)
String sql = "SELECT * FROM t WHERE v = '" + rs.getString("nickname") + "'";
stmt.execute(sql);
