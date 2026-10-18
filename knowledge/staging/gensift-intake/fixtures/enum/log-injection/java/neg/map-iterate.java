// 出处:人工构造(硬负例:Map 迭代)
for (Map.Entry<String, Long> e : stats.entrySet()) { sink.accept(e.getKey(), e.getValue()); }
