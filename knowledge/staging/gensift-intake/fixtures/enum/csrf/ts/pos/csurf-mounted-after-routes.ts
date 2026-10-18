// 出处:人工构造(依据 CWE-352 中间件挂载晚于写路由——顺序豁免)
app.post("/admin/purge", purgeHandler);
app.use(csurf({ cookie: true }));
