// 出处:人工构造(硬负例:流式集合操作)
long n = list.stream().filter(x -> x.length() > 2).count();
