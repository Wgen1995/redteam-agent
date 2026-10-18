// 出处:人工构造(硬负例:结构化 Filters 构建器)
collection.find(Filters.eq("status", statusValue)).sort(Sorts.ascending("sku"));
