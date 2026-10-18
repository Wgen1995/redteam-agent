// 出处:人工构造(依据 CWE-79 响应直出请求参数,反射型)
response.getWriter().print(req.getParameter("q"));
