// 出处:人工构造(噪音:同 API 安全用法——解析服务端常量;允许命中由五步判别)
const xml2js = require('xml2js');
xml2js.parseString(LOCALE_STRINGS_XML, (err, bundle) => i18n.register(bundle));
