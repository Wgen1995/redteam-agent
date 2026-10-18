// 出处:人工构造(依据 CWE-22 RandomAccessFile 拼接形态)
String blobKey = req.getParameter("key");
RandomAccessFile raf = new RandomAccessFile(chunkRoot + "/" + blobKey, "r");
