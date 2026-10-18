// 出处:人工构造(硬负例:配置读取)
@Value("${billing.retry.max}")
private int retryMax;
public Receipt settle(Order order) {
    return billingClient.settle(order, retryMax);
}
