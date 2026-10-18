// 出处:人工构造(依据 CWE-78 伪参数化：数组但第三元素整体经 shell)
Runtime.getRuntime().exec(new String[]{"/bin/sh", "-c", "cat " + req.getParameter("f")});
