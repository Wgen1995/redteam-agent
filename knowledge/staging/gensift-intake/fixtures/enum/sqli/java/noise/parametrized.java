// 出处:人工构造(噪音:同 API 安全用法——允许命中,由五步判别)
jdbcTemplate.queryForObject("SELECT cnt FROM t WHERE u=?", Integer.class, user);
