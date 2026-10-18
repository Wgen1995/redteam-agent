// 出处:人工构造(依据 CWE-89 二阶:服务层 getByX 回读用户偏好再拼接)
String sql = "DELETE FROM sessions WHERE tag = '" + userService.getByUserId(uid).getPref() + "'";
jdbcTemplate.execute(sql);
