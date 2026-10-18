// 出处:人工构造(硬负例:解析响应体字符串,消费侧)
JSONObject obj = new JSONObject(cachedBody);
String embedded = obj.optString("url", "");
return embedded.length();
