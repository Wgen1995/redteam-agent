// 出处:人工构造(硬负例:字符串组装)
StringBuilder sb = new StringBuilder("report-");
sb.append(tenant).append('-').append(year);
String cacheKey = sb.toString();
