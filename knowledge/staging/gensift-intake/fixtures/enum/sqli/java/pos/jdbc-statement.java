// 出处:人工构造(CWE-89 原生 Statement：创建点+执行点)
Statement stmt = conn.createStatement();
stmt.execute("UPDATE t SET v='" + value + "' WHERE id=" + id);
