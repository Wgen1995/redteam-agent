// 出处:人工构造(CWE-89 queryForRowSet 拼接)
SqlRowSet rs = jdbcTemplate.queryForRowSet("SELECT * FROM t WHERE u = '" + user + "'");
