// 出处:人工构造(依据 Jackson 2.10+ activateDefaultTyping 换名形态)
ObjectMapper mapper = new ObjectMapper(new JsonFactory());
mapper.activateDefaultTyping(ptv);
Object o = mapper.readValue(body, BaseMsg.class);
