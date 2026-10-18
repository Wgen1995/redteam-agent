// 出处:人工构造(硬负例:Map 迭代)
for (Map.Entry<String, Integer> e : counters.entrySet()) { emit(e.getKey(), e.getValue()); }
