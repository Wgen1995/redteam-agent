// 出处:人工构造(硬负例:外发 API 调用,常量目标)
public ExchangeRate fetchRate(String base) {
    return restTemplate.getForObject("https://api.internal/rates?base=" + base, ExchangeRate.class);
}
