// 出处:人工构造(噪音:同 API 安全用法——常量 registry URL,允许命中)
const meta = await got('https://registry.npmjs.org/left-pad').json();
return meta.version;
