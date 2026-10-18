// 出处:人工构造(依据 CWE-918 URL.openStream 图片代理形态)
String avatarUrl = user.getAvatarUrl();
InputStream in = new URL(avatarUrl).openStream();
IOUtils.copy(in, response.getOutputStream());
