// 出处:人工构造(硬负例:REST 控制器)
@PostMapping("/notes")
public Note create(@RequestBody NoteRequest req) { return service.create(req); }
