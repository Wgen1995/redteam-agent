// 出处:人工构造(硬负例:Kafka 发送)
kafkaTemplate.send("audit-" + tenant, eventJson);
