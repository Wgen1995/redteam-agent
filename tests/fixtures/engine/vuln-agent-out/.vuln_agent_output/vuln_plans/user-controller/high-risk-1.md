# 用户查询 - SQL 注入
**验证目标**：ORDER BY 注入
**疑点位置**：UserController.java:96
**疑点原因**：sort 参数直接拼接进 ORDER BY 子句，无白名单
**优先级**：高
