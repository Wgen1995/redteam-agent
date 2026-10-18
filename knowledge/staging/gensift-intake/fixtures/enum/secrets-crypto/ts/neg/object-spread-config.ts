// 出处:人工构造(硬负例:展开配置无字面凭据)
const cfg = { ...defaults, env: process.env.NODE_ENV, retries: 3 };
