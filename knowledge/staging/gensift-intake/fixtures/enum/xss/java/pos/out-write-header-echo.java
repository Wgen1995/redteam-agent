// 出处:人工构造(依据 CWE-79 回显请求头字段)
out.write(request.getHeader("X-Trace"));
