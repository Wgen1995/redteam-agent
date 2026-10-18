// 出处:人工构造(CWE-89 MyBatis @Update ${})
@Update("UPDATE config SET value = '${value}' WHERE key = '${key}'")
int updateConfig(@Param("key") String key, @Param("value") String value);
