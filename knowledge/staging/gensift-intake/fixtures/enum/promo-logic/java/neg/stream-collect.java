// 出处:人工构造(硬负例:集合流处理)
public Map<Long, List<Sku>> bySku(List<LineItem> items) {
    return items.stream().collect(Collectors.groupingBy(LineItem::getSkuId));
}
