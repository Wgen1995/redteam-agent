// 出处:人工构造(依据 CWE-1336 ejs 字符串模板)
const html = ejs.render(req.body.template, { user });
