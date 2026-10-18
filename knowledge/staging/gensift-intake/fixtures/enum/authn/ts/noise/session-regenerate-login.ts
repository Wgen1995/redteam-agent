// 出处:人工构造(噪音:登录后 regenerate 轮换+全属性 cookie)
app.post("/login", async (req, res) => {
  const user = await authenticate(req.body);
  await req.session.regenerate();
  req.session.userId = user.id;
  res.cookie("sessionid", req.sessionID, { httpOnly: true, secure: true, sameSite: "strict" });
  res.json({ ok: true });
});
