// 出处:人工构造(噪音:同 API 白名单重载——允许命中，由 C2 判别)
ParserConfig cfg = new ParserConfig();
cfg.setAutoTypeSupport(false);
cfg.addAccept("com.app.");
Object o = JSON.parseObject(text, cfg, Feature.SupportAutoType);
