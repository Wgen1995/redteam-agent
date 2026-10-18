// 出处:人工构造(硬负例:DB 连接串为常量,非 HTTP 外发)
Connection conn = DriverManager.getConnection("jdbc:postgresql://db.internal:5432/app", appUser, appPass);
PreparedStatement ps = conn.prepareStatement("select 1");
