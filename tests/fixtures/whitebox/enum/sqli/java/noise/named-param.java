// 出处:人工构造(噪音:MyBatis #{} 安全用法)
@Select("SELECT * FROM user WHERE name = #{name}")
User findByName(String name);
