// 出处:人工构造(硬负例:URI 解析无文件访问)
URI u = URI.create(rawTarget);
String host = u.getHost();
int port = u.getPort();
