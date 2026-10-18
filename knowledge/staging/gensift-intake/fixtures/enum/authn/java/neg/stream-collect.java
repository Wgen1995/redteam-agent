// 出处:人工构造(硬负例:流收集分组)
public Map<String, List<Order>> byCustomer(List<Order> orders) {
    return orders.stream().collect(Collectors.groupingBy(Order::getCustomerRef));
}
