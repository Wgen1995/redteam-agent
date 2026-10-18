// 出处:人工构造(硬负例:JSON 反序列化到强类型)
public PaymentIntent parse(String body) {
    return objectMapper.readValue(body, PaymentIntent.class);
}
