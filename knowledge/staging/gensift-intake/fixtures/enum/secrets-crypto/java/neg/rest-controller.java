// 出处:人工构造(硬负例:REST 控制器)
@PostMapping("/orders")
public Order create(@RequestBody OrderRequest req) { return service.create(req); }
