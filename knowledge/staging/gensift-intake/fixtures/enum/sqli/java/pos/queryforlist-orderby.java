// 出处:人工构造(ORDER BY 位置)
jdbcTemplate.queryForList("SELECT * FROM t ORDER BY " + sortCol);
