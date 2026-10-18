# 出处:人工构造(噪音:常量静态文件 send_file——允许命中)
return send_file(os.path.join(STATIC_DIR, 'style.css'))
