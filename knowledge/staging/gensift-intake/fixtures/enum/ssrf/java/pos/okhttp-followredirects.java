// 出处:人工构造(依据 CWE-918 OkHttp followRedirects 形态)
OkHttpClient client = new OkHttpClient.Builder().followRedirects(true).build();
Response response = client.newCall(new Request.Builder().url(nextUrl).build()).execute();
