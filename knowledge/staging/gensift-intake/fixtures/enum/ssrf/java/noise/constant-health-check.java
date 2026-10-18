// 出处:人工构造(噪音:固定常量 URL 的外发——host 编译期不可控,FP-1 参考)
private static final String STATUS_URL = "http://status.internal:9090/health";
HttpURLConnection conn = (HttpURLConnection) new URL(STATUS_URL).openConnection();
int code = conn.getResponseCode();
