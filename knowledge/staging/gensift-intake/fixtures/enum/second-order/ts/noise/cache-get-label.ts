// 出处:人工构造(噪音:缓存 get 回读拼接进问候文案——非解释器 sink)
const label = "Welcome back, " + userCache.get(token) + "!";
res.send(label);
