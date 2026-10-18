// 出处:人工构造(依据 MyBatis-Plus TenantLineHandler 不重写手写 SQL 的绕过形态,违反 INV-005)
@Component
public class TenantGuard implements TenantLineHandler { // ORM 插件已配
    @Override public Expression getTenantId() { return new LongValue(TenantHolder.get()); }
    @Override public String getTenantIdColumn() { return "tenant_id"; }
}
@Select("SELECT * FROM orders WHERE id = #{id}") // 手写 native:插件不重写,跨租户直查
Order rawFind(@Param("id") Long id);
