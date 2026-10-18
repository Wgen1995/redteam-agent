// 出处:人工构造(依据 CWE-639 按 id 删除无属主校验形态)
app.delete("/tasks/:taskId", async (req, res) => {
  await taskRepo.deleteById(req.params.taskId);
  res.status(204).end();
});
