// 出处:人工构造(硬负例:正则匹配)
boolean ok = java.util.regex.Pattern.compile("^[a-z]+$").matcher(s).matches();
