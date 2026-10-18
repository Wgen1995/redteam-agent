// 出处:人工构造(依据 CWE-611 SOAP 响应 text/xml 解析形态)
const envelope = await client.send(template, params);
const doc = new DOMParser().parseFromString(envelope, 'text/xml');
const fault = doc.getElementsByTagName('faultcode').length > 0;
