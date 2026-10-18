// 出处:人工构造(依据 CWE-117 log4j2 布局直排 %m 无 %enc)
builder = PatternLayout.newBuilder().withPattern("%d %p %c - %m%n").withConfiguration(config);
