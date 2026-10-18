// 出处:人工构造(依据 CWE-22 用户可控 id 拼文件名形态)
long uid = Long.parseLong(request.getParameter("uid"));
InputStream avatar = new FileInputStream(avatarRoot + "/" + uid + ".png");
File meta = new File(avatarRoot + "/" + uid + ".meta");
