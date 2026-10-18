// 出处:人工构造(依据 CWE-798 JWT secret 字面)
const auth = { secret: "jwt-hmac-s3cr3t-2024", expiry: "1h" };
app.use(jwt({ secret: auth.secret }));
