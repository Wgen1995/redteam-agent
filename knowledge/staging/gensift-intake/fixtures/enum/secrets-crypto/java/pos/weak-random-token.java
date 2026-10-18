// 出处:人工构造(依据 CWE-330/327 Random 生成会话令牌)
String token = Integer.toString(new Random().nextLong(), 36);
session.setAttribute("token", token);
