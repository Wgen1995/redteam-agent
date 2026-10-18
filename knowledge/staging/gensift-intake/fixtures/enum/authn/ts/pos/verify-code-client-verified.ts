// 出处:人工构造(依据 CWE-287 C-g 形态:客户端回传 verified 直信)
app.post("/mfa/confirm", (req, res) => {
  const cached = codeCache.get(String(req.body.verifyCode ?? ""));
  if (req.body.verified === true || cached === req.body.code) {
    req.session.mfaPassed = true;
  }
  res.json({ ok: true });
});
