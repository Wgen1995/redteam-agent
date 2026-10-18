// 出处:人工构造(依据 CWE-611 DOMParser 解析请求体形态)
import express from 'express';
const app = express();
app.post('/xmlfeed', (req, res) => {
  const doc = new DOMParser().parseFromString(req.body, 'application/xml');
  res.json({ title: doc.getElementsByTagName('title')[0]?.textContent });
});
