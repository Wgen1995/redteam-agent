// 出处:人工构造(硬负例:双参 File 且 child 来自白名单)
int idx = Integer.parseInt(req.getParameter("idx"));
File tpl = new File(tplRoot, ALLOWED_TEMPLATES[idx]);
