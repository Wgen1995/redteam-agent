// 出处:人工构造(依据 CWE-89 JDBC 形态)
String sql = "SELECT * FROM users WHERE name = '" + req.getParameter("name") + "'";
ResultSet rs = stmt.executeQuery(sql);
