// 出处:人工构造(硬负例:凭据外部化取值)
String dbPassword = System.getenv("DB_PASSWORD");
String dbUser = System.getenv("DB_USER");
Connection c = DriverManager.getConnection(url, dbUser, dbPassword);
