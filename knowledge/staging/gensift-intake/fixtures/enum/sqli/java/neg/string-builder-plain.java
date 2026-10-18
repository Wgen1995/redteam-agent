// 出处:人工构造(硬负例:普通字符串构造无 DB)
StringBuilder b = new StringBuilder("prefix-");
b.append(suffix).append("-suffix");
String s = b.toString();
