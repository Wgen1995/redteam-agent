// 出处:人工构造(依据 CVE-2019-10744 家族 defaultsDeep 递归写默认对象)
const cfg = _.defaultsDeep({}, req.body);
registry.set("tenant-config", cfg);
