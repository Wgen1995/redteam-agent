// 出处:人工构造(硬负例:哈希计算——密码学摘要非对象数据访问)
const digest = createHash("sha256").update(payload).digest("base64");
