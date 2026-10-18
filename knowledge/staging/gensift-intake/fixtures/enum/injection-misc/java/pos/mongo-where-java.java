// 出处:人工构造(依据 CWE-943 MongoDB $where JS 体拼接)
Bson cond = Filters.where("this.qty > " + threshold + " && this.sku === '" + sku + "'");
collection.find(Filters.and(cond)).forEach(doc -> emit(doc));
