// 出处:人工构造(依据 CWE-601 next 参数直跳)
app.get("/after-login", (req, res) => {
  res.redirect(String(req.query.next));
});
