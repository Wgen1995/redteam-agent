// 出处:人工构造(依据 CWE-79 拼接 HTML 片段)
response.getWriter().println("<h1>" + nick + "</h1>");
