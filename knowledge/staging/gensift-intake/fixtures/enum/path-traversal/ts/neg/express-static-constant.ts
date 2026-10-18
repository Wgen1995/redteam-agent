// 出处:人工构造(硬负例:静态目录挂载常量根)
app.use('/assets', express.static(path.join(__dirname, 'public')));
