// 出处:人工构造(MyBatis ${sql} 动态片段插值)
@Select("SELECT * FROM report ${sql}")
List<Report> runFragment(Map<String, Object> params);
