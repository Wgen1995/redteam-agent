// 出处:人工构造(噪音:activateDefaultTyping 配 PolymorphicTypeValidator 白名单——允许命中)
BasicPolymorphicTypeValidator ptv = BasicPolymorphicTypeValidator.builder().allowIfSubType("com.app.").build();
mapper.activateDefaultTyping(ptv);
Object o = mapper.readValue(body, Object.class);
