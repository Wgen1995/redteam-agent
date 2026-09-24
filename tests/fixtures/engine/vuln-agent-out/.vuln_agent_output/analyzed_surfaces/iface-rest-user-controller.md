### 关键控制点
**SQL 操作**：
    // UserController.java:96
    String sql = "SELECT id,name FROM users ORDER BY " + req.getParameter("sort");
    // 参数化 #{} 未应用于 ORDER BY 子句
**关键发现**：排序字段拼接进 SQL，无白名单校验
