// 出处:人工构造(依据 CWE-639 按 id 定位更新且请求体整体透传形态)
app.put("/users/:userId/profile", async (req, res) => {
  await userRepo.updateById(req.params.userId, req.body);
  res.status(204).end();
});
