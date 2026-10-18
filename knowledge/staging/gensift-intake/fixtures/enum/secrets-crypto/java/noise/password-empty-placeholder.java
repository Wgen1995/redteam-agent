// 出处:人工构造(噪音:空占位符形态——允许命中,VERIFY 按 C1 清零)
String password = "";
password = System.getenv().getOrDefault("DB_PASSWORD", password);
