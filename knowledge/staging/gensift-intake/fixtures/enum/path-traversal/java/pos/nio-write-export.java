// 出处:人工构造(依据 CWE-22 nio 写侧形态)
String rid = request.getParameter("rid");
OutputStream os = Files.newOutputStream(Paths.get(exportDir + "/" + rid + ".csv"));
Files.write(Paths.get(tmpDir + "/" + rid), payload);
FileOutputStream legacy = new FileOutputStream(archiveDir + "/" + rid + ".part");
