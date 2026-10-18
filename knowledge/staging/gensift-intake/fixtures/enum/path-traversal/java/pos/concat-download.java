// 出处:CVE-2020-17519 形态复刻(Apache Flink REST 任意文件读)
String name = req.getParameter("name");
File f = new File(docRoot + File.separator + name);
FileInputStream fis = new FileInputStream(docRoot + File.separator + name);
