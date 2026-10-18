// 出处:人工构造(硬负例:TypeReference 泛型固定)
List<User> users = JSON.parseObject(text, new TypeReference<List<User>>() {});
