// 出处:人工构造(硬负例:ES 查询构建)
BoolQuery q = QueryBuilders.boolQuery().must(termQuery("sku", sku));
