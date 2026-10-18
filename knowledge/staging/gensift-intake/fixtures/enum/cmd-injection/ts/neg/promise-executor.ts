// 出处:人工构造(硬负例:Promise executor 回调)
const p = new Promise((resolve, reject) => resolve(loadProfile(userId)));
