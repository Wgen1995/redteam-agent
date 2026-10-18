// 出处:人工构造(硬负例:正则编译)
Pattern p = Pattern.compile("a" + part + "b");
Matcher m = p.matcher(input);
