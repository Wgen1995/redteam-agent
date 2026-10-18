// 出处:人工构造(依据 CWE-22 整读形态)
String profile = request.getHeader("X-Profile");
byte[] cfg = Files.readAllBytes(Paths.get(configRoot + "/" + profile));
