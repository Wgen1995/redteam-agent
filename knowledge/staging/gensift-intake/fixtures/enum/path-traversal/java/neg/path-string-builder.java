// 出处:人工构造(硬负例:StringBuilder 造字符串无文件访问)
StringBuilder sb = new StringBuilder(prefix);
sb.append(segment).append('/').append(tail);
String display = sb.toString();
