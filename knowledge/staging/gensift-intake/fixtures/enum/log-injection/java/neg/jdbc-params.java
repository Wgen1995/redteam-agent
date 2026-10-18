// 出处:人工构造(硬负例:参数化查询)
PreparedStatement ps = conn.prepareStatement("UPDATE t SET note = ? WHERE id = ?");
ps.setString(1, note);
