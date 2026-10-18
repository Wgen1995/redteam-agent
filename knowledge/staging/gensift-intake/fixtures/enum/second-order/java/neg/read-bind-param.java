// 出处:人工构造(硬负例:回读值仅作绑定参数,无再拼接——C4 推翻形态)
User u = userRepository.findByName(name);
jdbcTemplate.queryForObject("SELECT cnt FROM t WHERE u = ?", Integer.class, u.getId());
