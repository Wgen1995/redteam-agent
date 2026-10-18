// 出处:人工构造(硬负例:常量 URL 请求)
const r = await fetch('https://api.internal/v1/health');
return r.json();
