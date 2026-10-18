// 出处:人工构造(硬负例:强摘要)
const checksum = crypto.createHash("sha256").update(buf).digest("hex");
