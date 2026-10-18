// 出处:人工构造(硬负例:Map.get 取默认值,非缓存回读拼接)
const v = map.get(key) ?? 0;
return v * 2;
