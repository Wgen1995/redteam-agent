// 出处:人工构造(硬负例:消息发送)
kafkaTemplate.send("orders-topic", new ProducerRecord<>(topic, key, payload));
