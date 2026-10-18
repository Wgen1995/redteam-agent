// 出处:人工构造(依据 CWE-434 formidable v3 调用形态)
const { formidable } = require('formidable');
export async function upload(req: any) {
  const form = formidable({ uploadDir: './public/uploads', keepExtensions: true });
  const { files } = await form.parse(req);
  return Object.values(files).map((f: any) => f.originalFilename);
}
