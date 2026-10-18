// 出处:人工构造(硬负例:reduce 浅聚合)
const byId = items.reduce<Record<string, Item>>((acc, it) => ({ ...acc, [it.id]: it }), {});
