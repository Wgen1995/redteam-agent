// 出处:人工构造(噪音:同 API + host 白名单形态——允许命中,Verifier 判据 C3 参考)
private static final Set<String> ALLOWED_HOSTS = Set.of("img.example.com", "cdn.example.com");
HttpUrl parsed = HttpUrl.parse(submittedUrl);
if (parsed == null || !ALLOWED_HOSTS.contains(parsed.host())) { return rejected(); }
OkHttpClient client = new OkHttpClient();
Response response = client.newCall(new Request.Builder().url(parsed).build()).execute();
