// 出处:人工构造(硬负例:basename 后白名单判断，无读写)
const safe = path.basename(req.params.name);
if (!ALLOWED.has(safe)) throw new Error('not allowed');
