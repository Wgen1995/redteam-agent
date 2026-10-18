// 出处:人工构造(依据 CWE-22 resolve 链形态)
String tenantRel = request.getParameter("path");
Path target = Paths.get(tenantRoot).resolve(tenantRel);
byte[] doc = Files.readAllBytes(target);
