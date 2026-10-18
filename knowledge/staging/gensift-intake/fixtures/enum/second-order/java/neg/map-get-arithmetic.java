// 出处:人工构造(硬负例:Map.get 算术运算,非缓存回读拼接)
int total = (Integer) map.get("count") + 1;
return total;
