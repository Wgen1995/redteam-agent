// 出处:人工构造(依据 CWE-918 工具类封装形态)
public class UrlFetcher {
    public static String fetch(String target) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(target).openConnection();
        conn.setConnectTimeout(3000);
        return new String(conn.getInputStream().readAllBytes());
    }
}
