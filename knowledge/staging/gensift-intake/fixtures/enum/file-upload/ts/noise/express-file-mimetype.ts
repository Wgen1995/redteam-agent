// 出处:人工构造(噪音:同 API 安全用法——类型白名单后转存对象存储;允许命中)
import multer from 'multer';
const upload = multer({ storage: multer.memoryStorage(), fileFilter: (_req, file, cb) => {
  cb(null, file.mimetype === 'image/png' || file.mimetype === 'image/jpeg');
}});
router.post('/badge', upload.single('badge'), async (req, res) => {
  await s3.putObject(BUCKET, `badges/${uuid()}.png`, req.file!.buffer);
});
