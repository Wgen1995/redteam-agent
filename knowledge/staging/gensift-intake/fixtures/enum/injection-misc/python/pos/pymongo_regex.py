# 出处:人工构造(依据 CWE-943 $regex 注入)
flt = {"email": {"$regex": request.json["pattern"], "$options": "i"}}
users = db.users.find(flt).limit(20)
