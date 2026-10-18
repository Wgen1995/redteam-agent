// 出处:人工构造(依据 CWE-79 Vue v-html 指令,内联模板字符串载体)
const tpl = `<div v-html="${rawSection}"></div>`;
