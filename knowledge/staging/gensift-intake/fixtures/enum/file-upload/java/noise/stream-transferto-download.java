// 出处:人工构造(噪音:形态撞车登记——InputStream.transferTo 为下载方向,非 MultipartFile)
java.nio.file.Files.newInputStream(java.nio.file.Path.of(EXPORT)).transferTo(resp.getOutputStream());
