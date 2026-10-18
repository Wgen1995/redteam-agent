// 出处:人工构造(依据 CWE-918 手工跟随重定向循环形态)
String next = req.getParameter("next");
HttpURLConnection conn = (HttpURLConnection) new URL(next).openConnection();
conn.setInstanceFollowRedirects(true);
