// 出处:人工构造(硬负例:哈希计算)
const digest = crypto.createHash('sha256').update(buf).digest('hex');
