// 出处:人工构造(依据 CWE-22 导出落盘形态)
const out = fs.createWriteStream(path.join(EXPORT_DIR, req.body.name));
out.write(chunk);
