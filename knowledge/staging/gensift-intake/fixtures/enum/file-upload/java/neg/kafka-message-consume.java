// 出处:人工构造(硬负例:消息消费无文件面)
@org.springframework.kafka.annotation.KafkaListener(topics = "billing.events")
public void onEvent(String payload) { ledger.append(payload); }
