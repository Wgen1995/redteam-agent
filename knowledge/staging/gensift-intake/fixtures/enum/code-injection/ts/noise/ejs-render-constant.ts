// 出处:人工构造(噪音:字面量模板,变量值可控归 xss 卡——允许命中)
const html = ejs.render("Hello <%= name %>", { name });
