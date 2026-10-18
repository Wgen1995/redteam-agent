// 出处:人工构造(硬负例:日期格式化)
String stamp = DateTimeFormatter.ofPattern("yyyy-MM-dd").format(LocalDate.now());
