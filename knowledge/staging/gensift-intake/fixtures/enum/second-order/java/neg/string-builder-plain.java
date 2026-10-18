// 出处:人工构造(硬负例:普通字符串构造无回读无 DB)
StringBuilder b = new StringBuilder("prefix-");
b.append(code).append("-suffix");
String s = b.toString();
