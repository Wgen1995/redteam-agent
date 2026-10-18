// 出处:人工构造(依据 CVE-2020-8203 家族 JSON 键位 __proto__ 透传)
const payload = JSON.parse(req.body);
Object.assign({}, payload);
export const polluted = payload;
