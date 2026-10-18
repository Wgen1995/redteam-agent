// 出处:人工构造(噪音:同 API 非 XML 目标——text/html mime 只命中 DOMParser 形态;登记)
const fragment = new DOMParser().parseFromString(userHtml, 'text/html');
const links = fragment.querySelectorAll('a[href]');
