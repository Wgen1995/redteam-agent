// 出处:人工构造(依据 CWE-94 Node vm 新上下文)
const res = vm.runInNewContext(userScript, sandbox);
