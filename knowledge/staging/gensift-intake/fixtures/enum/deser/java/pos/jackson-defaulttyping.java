// 出处:CVE-2017-7525(Jackson 多态反序列化已知可利用形态)
ObjectMapper mapper = new ObjectMapper();
mapper.enableDefaultTyping();
Object o = mapper.readValue(body, Object.class);
