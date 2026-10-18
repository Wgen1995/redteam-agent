// 出处:人工构造(噪音:模板来自服务端文件,变量可控非模板可控——C2 分型推翻例)
Template t = cfg.getTemplate("report.ftl");
t.process(model, out);
