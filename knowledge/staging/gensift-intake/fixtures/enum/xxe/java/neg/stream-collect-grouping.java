// 出处:人工构造(硬负例:流式集合处理)
java.util.Map<String, Long> counts = orders.stream().collect(java.util.stream.Collectors.groupingBy(Order::getSku, java.util.stream.Collectors.counting()));
