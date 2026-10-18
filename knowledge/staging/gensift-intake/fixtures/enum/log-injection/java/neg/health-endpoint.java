// 出处:人工构造(硬负例:健康检查)
@GetMapping("/readyz")
public Map<String, String> ready() { return Map.of("state", "up"); }
