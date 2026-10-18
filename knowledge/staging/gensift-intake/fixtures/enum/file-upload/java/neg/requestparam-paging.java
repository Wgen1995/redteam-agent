// 出处:人工构造(硬负例:分页参数)
public Page<Item> list(@RequestParam int page, @RequestParam int size) { return repo.findAll(PageRequest.of(page, size)); }
