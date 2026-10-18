// 出处:人工构造(依据 CWE-639 mongoose 按 id 直查无属主过滤形态)
app.get("/notes/:id", async (req, res) => {
  const note = await NoteModel.findById(req.params.id);
  res.json(note);
});
