// 出处:人工构造(硬负例:健康检查)
@GetMapping("/healthz")
public Map<String, String> health() { return Map.of("status", "ok"); }
