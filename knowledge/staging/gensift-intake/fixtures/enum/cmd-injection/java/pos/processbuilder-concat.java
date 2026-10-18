// 出处:人工构造(依据 CWE-78 sh -c 包装形态)
Process p = new ProcessBuilder("/bin/sh", "-c", "tar -czf " + archive + " " + dir).start();
