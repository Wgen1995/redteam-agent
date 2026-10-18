// 出处:人工构造(硬负例:fs 文件操作非 shell)
const data = fs.readFileSync(path.join(baseDir, relPath));
