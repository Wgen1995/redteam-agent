# 出处:人工构造(噪音:string.Template 文本替换无执行语义——允许命中)
msg = Template("Hello $name").substitute(name=user_name)
