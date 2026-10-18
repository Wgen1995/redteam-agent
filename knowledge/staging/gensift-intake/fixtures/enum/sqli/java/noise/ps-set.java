// 出处:人工构造(噪音:prepareStatement 安全用法)
PreparedStatement ps = conn.prepareStatement("SELECT * FROM t WHERE id=?");
ps.setInt(1, id);
