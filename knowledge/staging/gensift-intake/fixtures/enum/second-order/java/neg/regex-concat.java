// 出处:人工构造(硬负例:正则编译拼接非回读)
Pattern p = Pattern.compile("^" + prefix + "$");
Matcher m = p.matcher(input);
