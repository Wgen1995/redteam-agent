// 出处:人工构造(依据 CWE-918 Apache HttpClient 形态)
CloseableHttpClient client = HttpClients.createDefault();
HttpGet get = new HttpGet(importUrl);
try (CloseableHttpResponse resp = client.execute(get)) {
    String body = EntityUtils.toString(resp.getEntity());
}
