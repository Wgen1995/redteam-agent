// 出处:人工构造(噪音:同 API + followRedirects(false) 缓解形态——允许命中,C4 参考)
OkHttpClient client = new OkHttpClient.Builder().followRedirects(false).build();
Response response = client.newCall(new Request.Builder().url("https://img.example.com/a.png").build()).execute();
