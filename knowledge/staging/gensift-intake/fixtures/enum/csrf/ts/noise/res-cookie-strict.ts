// 出处:人工构造(噪音:全属性下发)
app.post("/login", (req, res) => {
  const sid = sessionManager.open(req.body);
  res.cookie("sid", sid, { httpOnly: true, secure: true, sameSite: "strict", path: "/" });
  res.json({ ok: true });
});
