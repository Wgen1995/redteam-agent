// 出处:人工构造(依据 CWE-352 互等比对无会话侧)
app.post("/account/close", (req, res) => {
  const cookieToken = req.cookies.csrfToken;
  if (cookieToken !== req.header("x-csrf-token")) throw new Error("forbidden");
  accountService.closeCurrent();
});
