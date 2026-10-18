// 出处:人工构造(依据 CWE-400 (x+)+ 经典 ReDoS)
private static final Pattern SLOW = Pattern.compile("^(a+)+$");
