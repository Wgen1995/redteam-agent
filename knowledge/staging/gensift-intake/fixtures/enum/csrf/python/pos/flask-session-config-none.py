# 出处:人工构造(依据 CWE-352 flask 会话 cookie 配置宽松形态)
app.config["SESSION_COOKIE_NAME"] = "sid"
app.config["SESSION_COOKIE_SAMESITE"] = None
app.config["SESSION_COOKIE_DOMAIN"] = ".parent-shop.com"
