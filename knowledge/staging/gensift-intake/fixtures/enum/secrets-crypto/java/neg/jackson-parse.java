// 出处:人工构造(硬负例:JSON 解析)
JsonNode node = mapper.readTree(body);
String tenant = node.path("tenant").asText();
