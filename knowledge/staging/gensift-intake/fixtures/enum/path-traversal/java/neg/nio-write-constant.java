// 出处:人工构造(硬负例:Files.write 常量路径)
Files.write(Path.of("/var/run/app.pid"), pidBytes);
Files.writeString(Path.of("/var/run/app.state"), state);
