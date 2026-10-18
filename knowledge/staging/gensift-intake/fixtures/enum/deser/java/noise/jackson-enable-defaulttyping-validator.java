// 出处:人工构造(噪音:enableDefaultTyping 带 validator 重载——允许命中)
mapper.enableDefaultTyping(ptv, ObjectMapper.DefaultTyping.NON_FINAL);
Object o = mapper.readValue(body, Object.class);
