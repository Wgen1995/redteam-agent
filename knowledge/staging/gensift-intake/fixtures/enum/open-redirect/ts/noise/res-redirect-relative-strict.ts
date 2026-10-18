// 出处:人工构造(噪音:相对路径强校验后跳转)
app.get("/next", (req, res) => {
  const to = String(req.query.to ?? "/dashboard");
  if (!to.startsWith("/") || to.startsWith("//") || to.includes("\\")) throw new Error("bad target");
  res.redirect(to);
});
