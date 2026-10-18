// 出处:人工构造(噪音:%replace 剥离换行——允许命中)
PatternLayout layout = PatternLayout.newBuilder().withPattern("%replace{%m}{[\r\n]}{ }%n").build();
