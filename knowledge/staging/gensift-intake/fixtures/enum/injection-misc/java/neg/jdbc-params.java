// 出处:人工构造(硬负例:参数化 SQL)
PreparedStatement ps = conn.prepareStatement("SELECT * FROM orders WHERE tenant = ?");
ps.setString(1, tenant);
