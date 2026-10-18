// 出处:人工构造(硬负例:ES 结构化查询构建器)
BoolQuery q = QueryBuilders.boolQuery().must(termQuery("sku", sku));
searchSource.query(q);
