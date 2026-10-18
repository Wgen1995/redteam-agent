// 出处:人工构造(依据 CWE-22 类路径资源读取形态)
String locale = request.getParameter("lang");
InputStream in = getClass().getResourceAsStream("/i18n/" + locale + ".properties");
