// 出处:人工构造(硬负例:JSON 解析)
JsonNode root = mapper.readTree(body);
String sku = root.path("sku").asText();
