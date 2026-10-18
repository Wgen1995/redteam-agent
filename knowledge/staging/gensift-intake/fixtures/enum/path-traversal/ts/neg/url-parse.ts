// 出处:人工构造(硬负例:URL 解析)
const u = new URL(req.query.next);
const dest = u.searchParams.get('to') ?? '/';
