# 出处:人工构造(噪音:random.choice 生成测试昵称——允许命中)
nickname = "".join(random.choice(WORDS) for _ in range(2))
