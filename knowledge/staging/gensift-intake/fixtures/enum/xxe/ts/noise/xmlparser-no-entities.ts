// 出处:人工构造(噪音:同 API 安全用法——processEntities 关闭)
const parser = new XMLParser({ processEntities: false, allowBooleanAttributes: false });
const internal = parser.parse(TEMPLATE_XML);
