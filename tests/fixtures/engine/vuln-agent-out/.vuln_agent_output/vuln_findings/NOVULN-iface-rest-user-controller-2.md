# 用户查询 - 按名检索注入猜想（排除）
**类型**：SQL 注入
**位置**：UserController.java:44
**CVSS 评分**：0.0
**严重性**：低
**复核排除**：参数化 #{} 已覆盖（nameFilter 全程 PreparedStatement 绑定），无拼接路径
**事实依据**：
    // UserController.java:44 - 全程参数化绑定
    ps.setString(1, req.getParameter("nameFilter"));
