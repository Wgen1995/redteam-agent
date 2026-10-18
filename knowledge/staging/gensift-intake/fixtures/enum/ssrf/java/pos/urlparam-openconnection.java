// 出处:人工构造(依据 CWE-918 HttpURLConnection 形态)
String target = req.getParameter("url");
HttpURLConnection conn = (HttpURLConnection) new URL(target).openConnection();
conn.setRequestMethod("GET");
