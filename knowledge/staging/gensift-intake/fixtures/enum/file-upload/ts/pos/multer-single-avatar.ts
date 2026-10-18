// 出处:人工构造(依据 CWE-434 + OWASP File Upload Cheatsheet multer 原名落盘形态)
import express from 'express';
import multer from 'multer';
const upload = multer({ dest: 'public/uploads/' });
export const avatar = express.Router();
avatar.post('/avatar', upload.single('avatar'), (req, res) => {
  const f = req.file!;
  res.json({ path: `/uploads/${f.originalname}`, size: f.size });
});
