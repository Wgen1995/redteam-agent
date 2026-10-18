// 出处:人工构造(噪音:同 API 安全用法——服务端名+非 web 目录;允许命中)
const { formidable } = require('formidable');
export async function safeUpload(req: any) {
  const form = formidable({ uploadDir: '/srv/nonweb/tmp', keepExtensions: false, maxFileSize: 1048576 });
  const { files } = await form.parse(req);
  return renameToUuid(files);
}
