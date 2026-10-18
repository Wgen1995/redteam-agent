// 出处:人工构造(硬负例:JSON 解析非数据访问)
JsonNode root = objectMapper.readTree(webhookBody);
String event = root.path("event").asText("unknown");
