# worklist.tsv

```
card_id	basis_id	direction	sink_type	module	band	status	depends_on	source	must_through
```

status ∈ {unchecked, blocked, disproved, not_applicable, no_path, blocked_at, candidate}。
source ∈ {inventory, neighborhood, hypothesis}。
band 由 worklist.py 计算，禁止手写与 sink_type 矛盾的值。
must_through 空则 K2 不准消（调用不清不级联）。
