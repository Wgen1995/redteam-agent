// 出处:人工构造(CWE-89 executeUpdate 拼接)
stmt.executeUpdate("INSERT INTO audit VALUES ('" + actor + "', '" + action + "')");
