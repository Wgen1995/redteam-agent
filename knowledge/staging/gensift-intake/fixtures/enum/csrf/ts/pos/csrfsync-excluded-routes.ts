// 出处:人工构造(依据 CWE-352 中间件豁免路由面——点状缺失)
const csrfSync = require("csrf-csrf");
app.use(csrfSync({ excludedRoutes: ["/api/transfer"] }));
app.post("/api/transfer", transferHandler);
