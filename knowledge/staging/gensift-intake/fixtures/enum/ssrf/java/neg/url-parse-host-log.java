// 出处:人工构造(硬负例:URL 仅解析取 host 做日志)
URI uri = URI.create(referer);
String host = uri.getHost();
logger.info("inbound referer host={}", host);
