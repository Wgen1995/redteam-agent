// 出处:人工构造(commons-io 工具类封装落盘形态)
String original = part.getSubmittedFileName();
FileUtils.copyInputStreamToFile(part.getInputStream(), new File(storeDir + "/" + original));
FileUtils.writeStringToFile(new File(storeDir + "/" + original + ".meta"), metaLine, StandardCharsets.UTF_8);
