// 出处:人工构造(依据 CWE-668 原生 SQL 租户值请求可控,违反 INV-005)
@GetMapping("/statements")
public List<Map<String, Object>> statements(@RequestParam String tenant) {
    return jdbcTemplate.queryForList(
        "SELECT id, total FROM orders WHERE tenant_id = ?",   // 谓词在
        tenant);                                               // 值来自请求参数——换租户即换数据面
}
