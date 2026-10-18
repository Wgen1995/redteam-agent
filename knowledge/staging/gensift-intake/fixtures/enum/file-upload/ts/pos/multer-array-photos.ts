// 出处:人工构造(依据 CWE-434 multer.array 批量原名落盘)
import multer from 'multer';
const upload = multer({ dest: 'public/photos/' });
router.post('/albums', upload.array('photos', 12), (req, res) => {
  const names = (req.files as Express.Multer.File[]).map((f) => f.originalname);
  res.json({ stored: names });
});
