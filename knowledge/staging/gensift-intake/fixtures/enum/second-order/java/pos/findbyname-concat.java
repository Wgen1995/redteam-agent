// 出处:人工构造(依据 CWE-89 二阶:写侧昵称入库,另一请求 Spring Data findByX 回读再拼 SQL)
@PostMapping("/profile")
public void update(@RequestBody ProfileDto dto) { userRepository.save(dto); }

String sql = "SELECT * FROM audit_log WHERE note = '" + userRepository.findByName(name).getNickname() + "'";
jdbcTemplate.update(sql);
