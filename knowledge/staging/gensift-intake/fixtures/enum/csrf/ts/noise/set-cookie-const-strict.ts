// 出处:人工构造(噪音:头常量直写全属性值)
const SET_COOKIE = "set-cookie";
app.post("/auth/sso", (req, res) => {
  res.setHeader(SET_COOKIE, `sid=${value}; Path=/; Secure; HttpOnly; SameSite=Strict`);
});
