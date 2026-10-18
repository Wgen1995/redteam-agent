// 出处:人工构造(依据 CWE-94 Node vm 复用上下文)
const res = vm.runInContext(ruleCode, ctx, { timeout: 100 });
