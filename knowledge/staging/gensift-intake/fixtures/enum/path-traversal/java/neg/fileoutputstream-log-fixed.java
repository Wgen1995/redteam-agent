// 出处:人工构造(硬负例:日志文件写入路径固定)
private final FileOutputStream audit = new FileOutputStream("/var/log/app/audit.log", true);
