// 出处:人工构造(噪音:原生 SQL 租户谓词+绑定值来自上下文——符合 INV-005)
public Optional<Order> find(Long id) {
    Long tenant = tenantContext.currentTenant();
    return jdbcTemplate.query(
        "SELECT * FROM orders WHERE tenant_id = ? AND id = ?",
        rowMapper, tenant, id); // 谓词在且绑定值服务端来源
}
