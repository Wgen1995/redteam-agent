// 出处:人工构造(依据 CWE-89 二阶:MyBatis selectOne 回读配置值再拼接)
String next = "UPDATE counters SET label = '" + sqlSession.selectOne("Cfg.getById", id) + "'";
sqlSession.update(next);
