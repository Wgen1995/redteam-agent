// 出处:人工构造(硬负例:null 原型承载用户键)
const safe: Record<string, unknown> = Object.create(null);
for (const [k, v] of Object.entries(req.body)) { safe[k] = v; }
