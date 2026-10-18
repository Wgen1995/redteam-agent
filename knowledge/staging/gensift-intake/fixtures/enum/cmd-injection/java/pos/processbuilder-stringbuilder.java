// 出处:人工构造(StringBuilder 链尾进命令)
StringBuilder cmd = new StringBuilder("mysqldump -u backup ");
cmd.append("--password=").append(pwd).append(" ").append(db);
new ProcessBuilder("/bin/sh", "-c", cmd.toString()).inheritIO().start();
