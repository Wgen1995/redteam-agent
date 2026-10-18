// 出处:人工构造(硬负例:时间格式化)
String stamp = DateTimeFormatter.ofPattern("yyyyMMdd").format(LocalDateTime.now());
