// 出处:人工构造(MyBatis 注解 ${})
@Select("SELECT * FROM user WHERE name = '${name}'")
User findByName(String name);
