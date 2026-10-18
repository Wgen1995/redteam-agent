// 出处:人工构造(依据 CWE-798 连接串内嵌口令)
Connection conn = DriverManager.getConnection("jdbc:mysql://db.internal:3306/app?user=admin&password=Pr0dPass&useSSL=false");
