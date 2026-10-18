// 出处:人工构造(噪音:fileId→服务端枚举映射查路径——允许命中,由 C1 判)
String mapped = REPORT_FILES.get(reportId);
File report = new File(reportDir + "/" + mapped);
return new FileInputStream(reportDir + "/" + mapped);
