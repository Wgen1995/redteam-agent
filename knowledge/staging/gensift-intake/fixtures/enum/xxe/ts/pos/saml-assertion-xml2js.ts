// 出处:人工构造(依据 CWE-611 SAML assertion 解码后 xml2js 解析——IdP 来源不可信)
const xml2js = require('xml2js');
const raw = Buffer.from(samlRequest.SAMLResponse, 'base64').toString('utf8');
xml2js.parseString(raw, (err, sso) => {
  if (err) throw err;
  session.user = sso['samlp:Response']?.assertion?.attributeStatement;
});
