// 出处:人工构造(依据 CWE-611 xml2js parseString 回调形态)
const xml2js = require('xml2js');
xml2js.parseString(req.body, { explicitArray: false }, (err, result) => {
  if (err) { res.status(400).end(); return; }
  orders.push(result.orders.item);
});
