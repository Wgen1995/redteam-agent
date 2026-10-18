// 出处:人工构造(依据 CWE-94 postMessage 数据直达 eval)
const cfg = eval(event.data);
