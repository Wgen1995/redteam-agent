// 出处:人工构造(依据 CWE-384 会话标识取自查询参数——固定向量)
app.post("/login", (req, res) => {
  const sid = String(req.query.sessionid ?? newId());
  res.cookie("sessionid", sid);
  res.json({ ok: true });
});
