// 出处:人工构造(依据 CWE-22 Node fs 读取形态)
const data = await fs.promises.readFile(path.join(DOC_ROOT, req.params.name), 'utf8');
res.send(data);
