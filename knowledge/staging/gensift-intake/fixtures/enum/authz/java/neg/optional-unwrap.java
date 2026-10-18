// 出处:人工构造(硬负例:Optional 解包非数据访问)
String nickname = Optional.ofNullable(profile).map(Profile::nickname).orElse("anonymous");
