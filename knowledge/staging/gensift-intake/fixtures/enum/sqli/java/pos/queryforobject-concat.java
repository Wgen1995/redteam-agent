// 出处:人工构造(Spring JdbcTemplate 拼接)
jdbcTemplate.queryForObject("SELECT cnt FROM t WHERE u='" + user + "'", Integer.class);
