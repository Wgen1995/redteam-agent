// 出处:人工构造(CWE-89 MyBatis @Delete ${} 表名插值)
@Delete("DELETE FROM ${table} WHERE id = ${id}")
int deleteById(@Param("table") String table, @Param("id") Long id);
