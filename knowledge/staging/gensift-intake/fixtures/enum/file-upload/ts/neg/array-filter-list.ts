// 出处:人工构造(硬负例:数组过滤——数组语义非 multer)
const visible = items.filter((i) => i.state === 'active').map((i) => i.sku);
