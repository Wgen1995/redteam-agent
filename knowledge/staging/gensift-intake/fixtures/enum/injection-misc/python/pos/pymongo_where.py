# 出处:人工构造(依据 CWE-943 pymongo $where)
query = {"$where": "this.price < " + request.args.get("cap")}
docs = list(db.products.find(query))
