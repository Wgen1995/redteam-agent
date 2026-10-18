// 出处:人工构造(噪音:null 原型目标 + 浅合并——允许命中)
const merged = Object.assign(Object.create(null), defaults, overrides);
