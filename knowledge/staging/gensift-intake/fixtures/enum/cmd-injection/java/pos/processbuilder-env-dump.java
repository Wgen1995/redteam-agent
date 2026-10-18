// 出处:人工构造(凭据拼接进命令)
ProcessBuilder pb = new ProcessBuilder("bash", "-c", "pg_dump -U " + dbUser + " -h " + dbHost + " " + dbName);
pb.environment().put("PGPASSWORD", pwd);
pb.start();
