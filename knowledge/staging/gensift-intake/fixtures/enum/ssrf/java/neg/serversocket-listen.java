// 出处:人工构造(硬负例:入站监听,非出站请求)
ServerSocket server = new ServerSocket(9090);
Socket clientSocket = server.accept();
