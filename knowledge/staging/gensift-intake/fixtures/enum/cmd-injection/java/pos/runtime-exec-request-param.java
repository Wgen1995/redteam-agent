// 出处:人工构造(依据 CWE-78 请求参数直达命令)
Runtime.getRuntime().exec("gzip -d " + req.getParameter("file"));
