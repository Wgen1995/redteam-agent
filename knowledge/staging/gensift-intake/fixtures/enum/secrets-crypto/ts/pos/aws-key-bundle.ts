// 出处:人工构造(依据 CWE-798 前端/脚本内嵌 AWS key 形态)
const AWS_ACCESS_KEY = "AKIAJ4RP2V7KZQ3XW8MG";
export const s3Client = new S3Client({ region, accessKeyId: AWS_ACCESS_KEY });
