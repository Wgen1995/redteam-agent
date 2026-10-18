// 出处:人工构造(硬负例:下载响应头设置——响应头写入易混形态)
public void download(ExportTask task, HttpServletResponse res) throws IOException {
    res.setHeader("Content-Disposition", "attachment; filename=\"report-" + task.id() + ".csv\"");
    exportWriter.write(task, res.getOutputStream());
}
