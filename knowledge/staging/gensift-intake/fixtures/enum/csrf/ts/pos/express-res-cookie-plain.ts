// 出处:人工构造(依据 CWE-352 会话 cookie 无 sameSite 选项形态)
app.post("/api/cart/add", (req, res) => {
  res.cookie("sid", req.session.id);
  cartService.add(req.body);
  res.json({ ok: true });
});
