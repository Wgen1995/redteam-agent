# 出处:人工构造(噪音:空占位符——允许命中)
password = ""
password = os.environ.get("DB_PASSWORD", password)
