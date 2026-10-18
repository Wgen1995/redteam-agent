// 出处:人工构造(硬负例:配置目录创建)
fs.mkdirSync(process.env.LOG_DIR ?? '/var/log/app', { recursive: true });
