// 出处:人工构造(噪音:Random 用于测试数据洗牌——允许命中)
List<Item> shuffled = new ArrayList<>(items);
Collections.shuffle(shuffled, new Random(42));
