// 出处:人工构造(硬负例:解析缓存的响应文本,消费侧)
const dto = JSON.parse(cachedText) as UserDto;
return dto.email;
