// 出处:人工构造(噪音:basename 净化后同 API 用法——允许命中)
const name = path.basename(req.params.name);
const cfg = fs.readFileSync(path.join(ROOT, name), 'utf8');
