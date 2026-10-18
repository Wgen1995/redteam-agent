# 出处:人工构造(依据 CWE-117 字符串 %-格式化后直排)
logger.info("user %s from %s" % (user, request.headers.get("User-Agent")))
