// 出处:人工构造(依据 CWE-79 cookie 值回显)
response.getWriter().print(cookie.getValue());
