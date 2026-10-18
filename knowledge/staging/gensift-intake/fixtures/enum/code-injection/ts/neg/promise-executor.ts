// 出处:人工构造(硬负例:Promise executor 非 eval)
const p = new Promise((resolve) => resolve(load(id)));
