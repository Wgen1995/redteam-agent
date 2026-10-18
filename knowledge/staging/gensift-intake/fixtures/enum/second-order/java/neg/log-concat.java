// 出处:人工构造(硬负例:拼接但无存储回读——请求头直达日志)
logger.info("user " + req.getHeader("X-User") + " viewed report");
