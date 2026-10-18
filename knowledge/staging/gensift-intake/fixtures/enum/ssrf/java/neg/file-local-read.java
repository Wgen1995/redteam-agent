// 出处:人工构造(硬负例:本地文件读取,非 URL 外发)
File f = new File(uploadDir, fileName);
byte[] content = Files.readAllBytes(f.toPath());
