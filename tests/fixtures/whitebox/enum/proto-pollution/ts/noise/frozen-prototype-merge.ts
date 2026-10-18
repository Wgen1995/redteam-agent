// 出处:人工构造(噪音:全局冻结兜底后 merge——允许命中)
Object.freeze(Object.prototype);
_.merge(dst, userPrefs);
