// 出处:人工构造(依据 CWE-22 nio 拼接形态)
String rel = request.getParameter("rel");
InputStream is = Files.newInputStream(Paths.get(docRoot + "/" + rel));
BufferedReader br = Files.newBufferedReader(Paths.get(confRoot + "/" + tenantName));
byte[] body = Files.readAllBytes(Paths.get(mailRoot + "/" + msgId + ".eml"));
