// 出处:人工构造(依据 CWE-117 异常 message 拼接)
logger.error("payment failed for " + userId + ": " + err.message);
