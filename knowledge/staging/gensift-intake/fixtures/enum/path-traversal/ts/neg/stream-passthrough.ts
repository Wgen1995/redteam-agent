// 出处:人工构造(硬负例:纯流转无文件访问)
const pt = new stream.PassThrough();
pt.pipe(process.stdout);
