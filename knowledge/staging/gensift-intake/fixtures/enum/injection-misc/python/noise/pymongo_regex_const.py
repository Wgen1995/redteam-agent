# 出处:人工构造(噪音:服务端自产 $regex——允许命中)
phones = db.users.find({"mobile": {"$regex": r"^1[3-9]\d{9}$"}})
