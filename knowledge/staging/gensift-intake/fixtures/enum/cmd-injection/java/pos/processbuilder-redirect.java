// 出处:人工构造(ProcessBuilder + 管道输出读取)
Process p = new ProcessBuilder("openssl", "s_client", "-connect", host + ":" + port).redirectErrorStream(true).start();
