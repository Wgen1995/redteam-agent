// 出处:人工构造(硬负例:普通字符串构造)
StringBuilder b = new StringBuilder("req-");
String traceId = b.append(zone).append('-').append(seq).toString();
