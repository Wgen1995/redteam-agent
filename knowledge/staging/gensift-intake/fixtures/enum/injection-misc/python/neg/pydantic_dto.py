# 出处:人工构造(硬负例:body 经 schema 白名单)
payload = LoginSchema.model_validate(request.json)
