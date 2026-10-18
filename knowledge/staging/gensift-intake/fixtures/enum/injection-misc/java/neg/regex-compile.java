// 出处:人工构造(硬负例:正则编译)
Pattern p = Pattern.compile("^[a-z]{2}-\\d{4}$");
Matcher m = p.matcher(code);
