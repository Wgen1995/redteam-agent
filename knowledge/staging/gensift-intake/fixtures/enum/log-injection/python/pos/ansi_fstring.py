# 出处:人工构造(依据 CWE-117 ANSI 转义随消息直排)
logger.info(f"\x1b[31m{message}\x1b[0m")
