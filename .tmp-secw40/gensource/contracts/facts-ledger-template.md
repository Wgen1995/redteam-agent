# facts.tsv

```
fact_id	type	scope	sink_type	function	component	src	dst	sink_id	blocks	evidence	confirmed	confirmed_by	timestamp
```

type ∈ {uncontrolled, intended, kills, propagates, no_edge, dead}。
confirmed ∈ {true, false}；false 或 evidence 空则改写器忽略。
type 仅允许上述集合；结论词不得写入 type。
