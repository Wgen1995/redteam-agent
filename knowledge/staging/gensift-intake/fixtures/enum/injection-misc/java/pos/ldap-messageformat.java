// 出处:人工构造(依据 CWE-90 MessageFormat 展开仍是拼接)
String filter = MessageFormat.format("(&(uid={0})(status=active))", request.getParameter("uid"));
SearchControls sc = new SearchControls();
ctx.search(base, filter, sc);
