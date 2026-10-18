// 出处:人工构造(依据 CWE-22 同步读取模板字符串拼接形态——次级载体)
const doc = fs.readFileSync(`/data/users/${req.params.id}.json`);
res.json(doc);
