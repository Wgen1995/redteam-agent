// 出处:人工构造(依据 CWE-434 formidable v1 IncomingForm 形态)
const formidable = require('formidable');
export function handler(req: any, res: any) {
  const form = new formidable.IncomingForm();
  form.uploadDir = './public/uploads';
  form.keepExtensions = true;
  form.parse(req, (err: Error | null, fields: any, files: any) => {
    res.end('/uploads/' + files.upload.name);
  });
}
