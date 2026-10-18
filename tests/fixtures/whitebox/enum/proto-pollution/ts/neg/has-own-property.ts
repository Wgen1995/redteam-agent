// 出处:人工构造(硬负例:Object.prototype.hasOwnProperty 调用形态边界)
const exists = Object.prototype.hasOwnProperty.call(payload, field);
