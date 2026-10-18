// 出处:人工构造(硬负例:ES 查询构建器非 SQL 文本)
BoolQuery q = QueryBuilders.boolQuery().must(termQuery("f", v));
searchSource.query(q);
