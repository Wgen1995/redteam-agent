// 出处:人工构造(依据 CWE-352 sameSite none+宽 domain 形态)
app.post("/auth/sso", (req, res) => {
  const sid = sessionManager.open(req.body.ticket);
  res.cookie("sid", sid, { domain: ".app-parent.com", sameSite: "none", secure: true });
  res.json({ ok: true });
});
