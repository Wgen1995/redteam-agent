// 出处:人工构造(硬负例:JSON 往返克隆剥掉原型键)
const plain = JSON.parse(JSON.stringify(rich));
