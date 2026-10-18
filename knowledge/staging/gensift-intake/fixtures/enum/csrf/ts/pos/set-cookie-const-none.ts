// 出处:人工构造(依据 CWE-352 头常量直写拼 SameSite=None 值)
const SET_COOKIE = "set-cookie";
app.post("/auth/sso", (req, res) => {
  const value = sessionManager.open(req.body.ticket);
  res.setHeader(SET_COOKIE, `sid=${value}; Path=/; SameSite=None`);
});
