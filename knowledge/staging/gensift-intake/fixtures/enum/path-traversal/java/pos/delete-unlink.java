// 出处:人工构造(依据 CWE-22 删除侧形态)
String victim = req.getParameter("f");
Files.delete(Paths.get(tmpRoot + "/" + victim));
Files.deleteIfExists(Paths.get(tmpRoot + "/" + victim + ".bak"));
