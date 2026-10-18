// 出处:人工构造(硬负例:临时文件无上传面)
java.io.File scratch = java.io.File.createTempFile("report-", ".csv");
scratch.deleteOnExit();
