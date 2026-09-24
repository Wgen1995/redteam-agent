# 攻击面条目
- **类型**：iface
- **分类**：REST
- **来源**：src/main/java/com/acme/user/UserController.java:31:listUsers
- **描述**：用户列表查询接口 GET /api/users（分页+排序）
- **发现**：sort 参数直传后端 SQL 拼接，疑似注入点
