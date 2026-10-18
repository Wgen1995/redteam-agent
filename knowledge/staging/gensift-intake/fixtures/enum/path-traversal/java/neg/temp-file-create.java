// 出处:人工构造(硬负例:临时文件服务端生成名)
File tmp = File.createTempFile("report-", ".csv");
Path scratch = Files.createTempDirectory("import-");
