// 出处:人工构造(硬负例:无凭据外连)
URLConnection conn = new URL("https://api.internal.example/v1/ping").openConnection();
conn.setConnectTimeout(3000);
