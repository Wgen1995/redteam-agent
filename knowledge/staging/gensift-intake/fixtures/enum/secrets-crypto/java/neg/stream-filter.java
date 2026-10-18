// 出处:人工构造(硬负例:流处理)
List<Item> active = items.stream().filter(i -> i.getStatus() == Status.ACTIVE).collect(Collectors.toList());
