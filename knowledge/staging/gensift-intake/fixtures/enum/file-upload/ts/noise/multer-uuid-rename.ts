// 出处:人工构造(噪音:FP 卡形态——diskStorage UUID 改名+扩展名白名单;允许命中)
import multer from 'multer';
import { v4 as uuid } from 'uuid';
const storage = multer.diskStorage({
  destination: '/srv/nonweb/uploads',
  filename: (_req, file, cb) => {
    const ext = ALLOWED_EXT.has(file.originalname.split('.').pop()!.toLowerCase()) ? '.' + file.originalname.split('.').pop() : '';
    cb(null, uuid() + ext);
  },
});
export const upload = multer({ storage, limits: { fileSize: 2 * 1024 * 1024 } });
