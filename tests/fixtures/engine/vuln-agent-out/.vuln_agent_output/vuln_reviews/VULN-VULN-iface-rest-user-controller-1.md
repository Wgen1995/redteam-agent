# 复核：用户查询 - SQL 注入（维持 VULN）
**复核结论**：维持——ORDER BY 拼接无白名单成立，payload 语义在 ORDER BY 上下文可用；网关不过滤查询参数。
