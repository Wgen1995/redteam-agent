// 出处:人工构造(噪音:中间件默认全路由覆盖)
const csrfSync = require("csrf-csrf");
app.use(csrfSync({}));
app.post("/transfer", transferHandler);
