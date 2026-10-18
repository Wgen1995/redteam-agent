// 出处:人工构造(依据 CWE-117 参数拼接进日志)
logger.info("user " + req.getParameter("name") + " logged in from " + req.getRemoteAddr());
