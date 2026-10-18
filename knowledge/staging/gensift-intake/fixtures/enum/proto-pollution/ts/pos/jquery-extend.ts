// 出处:人工构造(依据 CVE-2018-3721 家族 extend 深合并形态)
const opts = $.extend(true, {}, defaults, req.query);
engine.run(opts);
