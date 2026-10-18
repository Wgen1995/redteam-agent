// 出处:人工构造(硬负例:流式操作)
long n = items.stream().filter(i -> i.length() > 3).count();
