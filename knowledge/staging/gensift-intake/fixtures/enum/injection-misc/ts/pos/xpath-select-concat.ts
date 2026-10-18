// 出处:人工构造(依据 CWE-643 xpath 库 select 拼接)
const nodes = xpath.select("/users/user[@name='" + req.params.name + "']", doc);
