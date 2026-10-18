// 出处:人工构造(依据 CWE-1336 Freemarker 字符串模板构造)
Template t = new Template("user", new StringReader(userTemplate), cfg);
t.process(model, out);
