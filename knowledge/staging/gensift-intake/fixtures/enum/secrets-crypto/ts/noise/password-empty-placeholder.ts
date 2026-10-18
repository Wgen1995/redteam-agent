// 出处:人工构造(噪音:空占位符——允许命中)
const config = { host, user, password: "" };
config.password = process.env.DB_PASSWORD ?? "";
