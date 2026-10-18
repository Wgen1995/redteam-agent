// 出处:人工构造(依据 CWE-94 Function 构造器)
const f = new Function("return " + userCode);
