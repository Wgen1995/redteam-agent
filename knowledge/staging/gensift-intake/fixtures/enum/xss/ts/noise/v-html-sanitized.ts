// 出处:人工构造(噪音:v-html 接净化产物)
const tpl = `<div v-html="${DOMPurify.sanitize(section)}"></div>`;
