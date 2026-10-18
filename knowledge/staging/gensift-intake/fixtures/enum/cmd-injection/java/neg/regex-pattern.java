// 出处:人工构造(硬负例:正则编译)
Pattern p = Pattern.compile("^order-" + tenant + "-[0-9]+$");
Matcher m = p.matcher(input);
