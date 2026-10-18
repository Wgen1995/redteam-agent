// 出处:人工构造(依据 CWE-78 Runtime.exec 拼接形态)
Runtime.getRuntime().exec("ping -c 1 " + host);
