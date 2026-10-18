// 出处:人工构造(依据 CWE-611 fast-xml-parser 服务端解析形态)
import { XMLParser } from 'fast-xml-parser';
const parser = new XMLParser({ ignoreAttributes: false });
const saml = Buffer.from(req.body.b64assertion, 'base64').toString('utf8');
const assertion = parser.parse(saml);
