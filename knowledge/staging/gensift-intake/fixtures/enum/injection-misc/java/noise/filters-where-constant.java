// 出处:人工构造(噪音:常量 JS 体——允许命中)
Bson guard = Filters.where("this.qty > this.reorderLevel");
collection.find(guard);
