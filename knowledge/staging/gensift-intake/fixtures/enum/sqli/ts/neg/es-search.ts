// 出处:人工构造(硬负例:ES 查询构建)
const r = await es.search({ query: { term: { f: v } } });
