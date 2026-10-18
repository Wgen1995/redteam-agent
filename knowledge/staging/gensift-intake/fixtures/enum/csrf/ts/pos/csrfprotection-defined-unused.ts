// 出处:人工构造(依据 CWE-352 防护中间件已定义未挂到写路由)
const csrfProtection = require("csurf")();
app.post("/transfer", transferHandler);
