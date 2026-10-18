// 出处:人工构造(依据 CWE-798 硬编码口令)
String password = "Sup3rS3cret!2024";
Connection c = DriverManager.getConnection(url, user, password);
