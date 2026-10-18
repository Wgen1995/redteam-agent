// 出处:人工构造(噪音:回读值作绑定参数——安全用法,弱锚不命中)
jdbcTemplate.queryForObject("SELECT cnt FROM t WHERE u = ?", Integer.class, userService.getByUserId(uid).getId());
