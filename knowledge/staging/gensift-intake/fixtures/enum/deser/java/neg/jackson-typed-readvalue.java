// 出处:人工构造(硬负例:Jackson 固定目标类型读取，类型不由载荷决定)
User u = mapper.readValue(json, User.class);
