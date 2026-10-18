// 出处:人工构造(硬负例:常量 URL 打开)
InputStream health = new URL("https://api.internal/health").openStream();
