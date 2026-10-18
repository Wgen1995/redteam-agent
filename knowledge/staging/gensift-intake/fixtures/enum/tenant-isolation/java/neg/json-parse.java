// 出处:人工构造(硬负例:固定类型 JSON 解析)
public User parse(String body) throws Exception {
    return new ObjectMapper().readValue(body, User.class);
}
