// 出处:人工构造(依据 CWE-918 OkHttp 形态)
OkHttpClient client = new OkHttpClient();
Request request = new Request.Builder().url(callbackParam).build();
Response response = client.newCall(request).execute();
String body = response.body().string();
