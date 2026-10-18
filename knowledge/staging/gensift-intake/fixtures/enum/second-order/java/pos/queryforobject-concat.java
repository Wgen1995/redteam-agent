// 出处:人工构造(依据 CWE-89 二阶:JdbcTemplate 回读上一条存储值直接进下一条拼接)
String sql = "SELECT * FROM mail_queue WHERE hdr = '" + jdbcTemplate.queryForObject(prevSql, String.class) + "'";
jdbcTemplate.queryForList(sql);
