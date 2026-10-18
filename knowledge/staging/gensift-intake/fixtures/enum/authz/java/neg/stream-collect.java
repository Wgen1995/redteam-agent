// 出处:人工构造(硬负例:流式聚合无按键取对象)
List<String> emails = users.stream().map(User::primaryEmail).filter(Objects::nonNull).collect(Collectors.toList());
