// 出处:人工构造(硬负例:REST 控制器)
@GetMapping("/items/{id}")
public Item get(@PathVariable String id) { return service.load(id); }
