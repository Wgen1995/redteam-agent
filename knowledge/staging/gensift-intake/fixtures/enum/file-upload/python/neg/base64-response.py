# 出处:人工构造(硬负例:base64 回吐常量)
inline = base64.b64encode(open(PLACEHOLDER_PNG, 'rb').read()).decode()
