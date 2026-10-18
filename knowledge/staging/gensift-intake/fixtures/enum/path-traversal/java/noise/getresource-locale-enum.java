// 出处:人工构造(噪音:locale 由服务端枚举映射——允许命中)
String res = SUPPORTED.get(lang);
InputStream in = getClass().getResourceAsStream("/bundles/" + res + ".properties");
